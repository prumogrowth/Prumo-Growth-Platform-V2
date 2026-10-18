/**
 * WA-01D: isolated Meta webhook GET ownership challenge, not an HTTP endpoint.
 * No live Meta calls, callbacks, Supabase, token persistence or channel updates.
 * The caller must select the verify token from a TRUSTED per-app configuration.
 */

const encoder = new TextEncoder();
const MAX_QUERY_BYTES = 8192;
const VERIFY_KEYS = ['hub.mode', 'hub.verify_token', 'hub.challenge'] as const;

export type GetChallengeDecision =
  | {
      readonly status: 200;
      readonly body: string;
      readonly headers: {
        readonly 'content-type': 'text/plain; charset=utf-8';
        readonly 'cache-control': 'no-store';
      };
    }
  | {
      readonly status: 403;
      readonly body: '';
      readonly headers: {
        readonly 'content-type': 'text/plain; charset=utf-8';
        readonly 'cache-control': 'no-store';
      };
    };

const headers = {
  'content-type': 'text/plain; charset=utf-8',
  'cache-control': 'no-store',
} as const;
const forbidden = (): GetChallengeDecision => ({ status: 403, body: '', headers });

/**
 * Compare token digests with a fixed-length XOR scan. The input strings are
 * never included in errors, results or logs. Length is bounded upstream.
 */
async function sameToken(actual: string, expected: string): Promise<boolean> {
  const digests = await Promise.all([
    crypto.subtle.digest('SHA-256', encoder.encode(actual)),
    crypto.subtle.digest('SHA-256', encoder.encode(expected)),
  ]);
  const a = new Uint8Array(digests[0]);
  const b = new Uint8Array(digests[1]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

/**
 * Evaluate a URL query string only. The host MUST already have resolved the
 * intended App by trusted routing/configuration, never from these parameters.
 * The successful challenge is NOT proof that a channel is registered or active.
 * A POST uses a different App Secret and its independent HMAC verification.
 */
export async function inspectMetaVerifyGet(
  rawQuery: string,
  trustedVerifyToken: string,
): Promise<GetChallengeDecision> {
  if (typeof trustedVerifyToken !== 'string' || trustedVerifyToken.length === 0 ||
      encoder.encode(trustedVerifyToken).byteLength > 1024) {
    // Configuration error; do not expose the token or return a false 200.
    throw new TypeError('Trusted Meta verify token is not configured');
  }
  if (typeof rawQuery !== 'string' || encoder.encode(rawQuery).byteLength > MAX_QUERY_BYTES ||
      rawQuery.includes('#')) return forbidden();

  const params = new URLSearchParams(rawQuery.startsWith('?') ? rawQuery.slice(1) : rawQuery);
  if ([...params.keys()].length !== VERIFY_KEYS.length ||
      VERIFY_KEYS.some((name) => params.getAll(name).length !== 1)) {
    return forbidden();
  }
  const mode = params.get('hub.mode');
  const receivedToken = params.get('hub.verify_token');
  const challenge = params.get('hub.challenge');
  // The Meta challenge is an integer string; preserve its exact characters.
  if (mode !== 'subscribe' || receivedToken === null ||
      challenge === null || !/^[0-9]{1,32}$/.test(challenge)) {
    return forbidden();
  }
  const matches = await sameToken(receivedToken, trustedVerifyToken);
  return matches ? { status: 200, body: challenge, headers } : forbidden();
}
