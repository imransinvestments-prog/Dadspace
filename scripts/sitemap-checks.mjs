export function isUnreleasedForumUrl(url) {
  const pathname=new URL(url).pathname
  return pathname==='/forum'||pathname.startsWith('/forum/')
}
