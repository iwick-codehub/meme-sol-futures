#!/usr/bin/env python3
"""Sync the crypto section to the Instar Brands Shopify store.

Repo is canon: body_*.html files here are the source of truth; this tool
upserts them as Online Store pages via the Admin API (GraphQL).

- New pages are created UNPUBLISHED (hidden). Publication is a human act,
  gated per futures/shopify/README.md.
- Existing pages are updated in place; their published/hidden state is
  NEVER changed by this tool.

Usage: python3 publish.py            # upsert all pages
"""
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
API_VERSION = "2026-07"

PAGES = [
    {"handle": "crypto", "title": "Crypto", "body_file": "body_crypto.html"},
    {"handle": "meme-futures", "title": "Meme Coin Futures", "body_file": "body_meme_futures.html"},
    {"handle": "acm-bid-board", "title": "The $ACM Bid Board", "body_file": "body_acm_bid_board.html"},
    {"handle": "acm", "title": "Aladdin's Castle | $ACM", "body_file": "body_acm.html"},
]


def env() -> dict:
    out = {}
    for line in (REPO / ".shopify.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def mint_token(e: dict) -> str:
    body = json.dumps({
        "client_id": e["SHOPIFY_CLIENT_ID"],
        "client_secret": e["SHOPIFY_CLIENT_SECRET"],
        "grant_type": "client_credentials",
    }).encode()
    req = urllib.request.Request(
        f"https://{e['SHOPIFY_STORE']}/admin/oauth/access_token",
        body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["access_token"]


def gql(e: dict, token: str, query: str, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        f"https://{e['SHOPIFY_STORE']}/admin/api/{API_VERSION}/graphql.json",
        body, {"Content-Type": "application/json", "X-Shopify-Access-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("errors"):
        raise SystemExit(f"GraphQL errors: {data['errors']}")
    return data["data"]


def find_page(e, token, handle):
    data = gql(e, token, """
      query($q: String!) { pages(first: 1, query: $q) {
        nodes { id title handle isPublished } } }""", {"q": f"handle:{handle}"})
    nodes = data["pages"]["nodes"]
    return nodes[0] if nodes else None


def upsert(e, token, spec) -> str:
    body_html = (HERE / spec["body_file"]).read_text()
    existing = find_page(e, token, spec["handle"])
    if existing:
        data = gql(e, token, """
          mutation($id: ID!, $page: PageUpdateInput!) {
            pageUpdate(id: $id, page: $page) {
              page { id handle isPublished }
              userErrors { field message } } }""",
            {"id": existing["id"], "page": {"title": spec["title"], "body": body_html}})
        result, verb = data["pageUpdate"], "updated"
    else:
        data = gql(e, token, """
          mutation($page: PageCreateInput!) {
            pageCreate(page: $page) {
              page { id handle isPublished }
              userErrors { field message } } }""",
            {"page": {"title": spec["title"], "handle": spec["handle"],
                      "body": body_html, "isPublished": False}})
        result, verb = data["pageCreate"], "created"
    if result["userErrors"]:
        raise SystemExit(f"{spec['handle']}: {result['userErrors']}")
    page = result["page"]
    state = "PUBLISHED" if page["isPublished"] else "hidden"
    num = page["id"].rsplit("/", 1)[-1]
    admin = f"https://admin.shopify.com/store/{e['SHOPIFY_STORE'].split('.')[0]}/pages/{num}"
    return f"{verb} /pages/{page['handle']} ({state}) -> {admin}"


if __name__ == "__main__":
    e = env()
    token = mint_token(e)
    for spec in PAGES:
        print(upsert(e, token, spec))
