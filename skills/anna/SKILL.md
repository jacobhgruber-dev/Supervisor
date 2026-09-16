---
name: anna
description: >
  Search Anna's Archive for books (incl. audiobooks) and academic articles, and download them.
  ONLY use this skill when the user types /anna anywhere in their message, invokes Anna's
  Archive by name, or says things like "go find this on Anna's", "check /anna for this",
  "use the Anna's framework", "search Anna's Archive for", "through Anna's", "from Anna's",
  etc. Do NOT trigger on generic mentions of "book", "paper", "article", "PDF", "academic
  research", or "download" alone — those could mean other sources (Google Scholar, JSTOR,
  local files, web search, etc.). The user must clearly intend Anna's Archive as the source.
  This skill wraps the annas-mcp CLI tool.
allowed-tools: Bash(git:*), Bash(go:*), Bash(cd:*), Bash(./annas-mcp:*), Bash(mkdir:*), Bash(cp:*), Bash(nano:*), Bash(mv:*)
---

# Anna's Archive — Book and Article Search/Download

Source repo: https://github.com/jacobhgruber-dev/anna-archive-cli — not publicly accessible (GitHub returns 404 as of 2026-09-16), so the repo must be made available to the user before this skill can work.
This skill requires the `annas-mcp` binary and a user-supplied Anna's Archive API key. Nothing is pre-configured: a new user must clone/build the tool and set the key themselves (see Setup).

## Setup (run once if binary missing)

Install dir: `$HOME/.local/share/anna` (~/.local/share/anna). Override with the `ANNA_HOME` env var if you keep it elsewhere.

Prerequisite: the user must have access to the tool repo. If `https://github.com/jacobhgruber-dev/anna-archive-cli` is not shared with them, stop and say so — the clone will 404.

If `$HOME/.local/share/anna/annas-mcp` does not exist:

```
git clone https://github.com/jacobhgruber-dev/anna-archive-cli.git $HOME/.local/share/anna
cd $HOME/.local/share/anna && go build -o annas-mcp ./cmd/annas-mcp
cp .env.example .env
mkdir -p $HOME/.local/share/anna/downloads
# Then: nano .env to set ANNAS_SECRET_KEY (your own Anna's Archive API key)
```

## Book Search

Run: `cd $HOME/.local/share/anna && ./annas-mcp book-search "<query>"`

- For audiobooks, include "audiobook mp3 m4b" in the query
- For exact titles, use quotes: "Pride and Prejudice" author name
- Show results in a clean table with #, Title, Author, Format, Size, Hash

## Book Download

When user asks to download a book result, use the hash from the search:

```
cd $HOME/.local/share/anna && ./annas-mcp book-download <md5_hash> "Title.ext"
```

- Extension must match the format from search results (epub, pdf, mp3, m4b, etc.)
- No need to ask for confirmation if the user said "download #3" — just do it
- Downloads go to `$HOME/.local/share/anna/downloads` (set in .env)

## Article / Paper Search

Run: `cd $HOME/.local/share/anna && ./annas-mcp article-search "<query>"`

- Searches Anna's Archive journal content specifically (content=journal in the URL)
- Auto-detects DOIs: if query starts with "10." it does a direct DOI lookup (returns single paper)
- For keyword searches (e.g., "neural networks transformers"), returns multiple results
- Show results in a clean table with #, Title, Authors, Journal, Size, Hash
- If user asks for a paper by DOI, use this command with the DOI

## Article / Paper Download

Run: `cd $HOME/.local/share/anna && ./annas-mcp article-download "<doi>"`

- Provide the DOI (starts with "10.") from search results or direct lookup
- Tries fast download (API key) first, falls back to SciDB download (no auth needed)
- Downloads go to `$HOME/.local/share/anna/downloads` (set in .env)
- No need to ask for confirmation — just download

## Output

Keep results concise: numbered table, basic metadata. Only show download command on request.

## Common Workflows

1. **"Find me [book title] by [author]"** → `book-search` with the title and author
2. **"Download the PDF of [book]"** → search first, then `book-download` with the hash
3. **"Find papers about [topic]"** → `article-search` with keywords
4. **"Get this paper: [DOI]"** → `article-search` with the DOI string, then `article-download`
5. **"Parse this PDF I just downloaded"** → use `pdftotext` on the downloaded file
