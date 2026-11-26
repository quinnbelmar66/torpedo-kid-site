// Latest Instagram posts, fetched once at build time from a Behold JSON feed
// (https://behold.so/docs/json-feeds). Images are downloaded and served from
// this site, so visitors never load anything from Instagram or Behold.
// Returns [] when no feed is configured or the feed can't be reached, and the
// page then shows a "Follow us" panel instead.
import { instagramFeed } from '~/site';

export interface InstagramPost {
  id: string;
  permalink: string;
  src: string;
  width: number;
  height: number;
  alt: string;
}

interface BeholdSize {
  mediaUrl: string;
  width: number;
  height: number;
}

interface BeholdPost {
  id: string;
  permalink: string;
  mediaType: string;
  altText?: string;
  prunedCaption?: string;
  sizes?: { small?: BeholdSize; medium?: BeholdSize; large?: BeholdSize };
}

let cache: Promise<InstagramPost[]> | undefined;

const describe = (p: BeholdPost) => {
  if (p.altText) return p.altText;
  const caption = (p.prunedCaption ?? '').replace(/\s+/g, ' ').trim();
  if (!caption) return 'Instagram post from the TorpedoKid team';
  return caption.length > 140 ? caption.slice(0, 137).trimEnd() + '…' : caption;
};

export const getInstagramPosts = (limit = 6): Promise<InstagramPost[]> => {
  if (!instagramFeed) return Promise.resolve([]);
  cache ??= (async () => {
    try {
      const res = await fetch(instagramFeed, { signal: AbortSignal.timeout(10_000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { posts?: BeholdPost[] };
      return (data.posts ?? [])
        .map((p) => ({ p, size: p.sizes?.medium ?? p.sizes?.large ?? p.sizes?.small }))
        .filter(({ size }) => size?.mediaUrl)
        .map(({ p, size }) => ({
          id: p.id,
          permalink: p.permalink,
          src: size!.mediaUrl,
          width: size!.width,
          height: size!.height,
          alt: describe(p),
        }));
    } catch (error) {
      console.warn(`[instagram] feed not loaded, showing the follow panel instead: ${error}`);
      return [];
    }
  })();
  return cache.then((posts) => posts.slice(0, limit));
};
