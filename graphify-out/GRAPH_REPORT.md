# Graph Report - WhatsApp-Web-session----sheets-using----service-Bot  (2026-09-25)

## Corpus Check
- 8 files · ~5,486 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 100 nodes · 106 edges · 19 communities (8 shown, 11 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]

## God Nodes (most connected - your core abstractions)
1. `WebBridgeClient` - 13 edges
2. `WhatsApp Web Session to Google Sheets Automation Bot` - 8 edges
3. `parse_record()` - 6 edges
4. `SheetsSyncer` - 6 edges
5. `💡 How It Works & Key Engineering Solutions` - 6 edges
6. `run_all()` - 5 edges
7. `🚀 Setup & Usage Guide` - 4 edges
8. `run_scrape()` - 3 edges
9. `run_sync()` - 3 edges
10. `CLI Commands` - 3 edges

## Surprising Connections (you probably didn't know these)
- `run_scrape()` --calls--> `WebBridgeClient`  [INFERRED]
  main.py → webbridge_client.py
- `run_sync()` --calls--> `SheetsSyncer`  [INFERRED]
  main.py → sheets_syncer.py

## Communities (19 total, 11 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (10): Client for interacting with real browser sessions via Kimi WebBridge. Handles ta, Extract the image from the currently active slide in the viewer., Click the 'Next' button to advance the gallery rightward., Click the 'Previous' button to navigate backwards., Scroll through all open transactions to the rightmost end.         Saves each fu, Send an action command to the WebBridge daemon., Borrow the foreground WhatsApp tab from the user's browser.         Matches the, Run JavaScript in the context of the active tab page. (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): 1. Active Tab Borrowing (Zero Re-authentication), 2. Center-Distance Carousel Algorithm, 3. Zero-Taint Canvas Frame Capture, 4. Native Windows WinRT OCR (`Windows.Media.Ocr`), 5. Automated Google Sheets Synchronization, code:mermaid (flowchart TD), code:mermaid (sequenceDiagram), code:block3 (├── config.py             # Global configuration, endpoints,) (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.24
Nodes (5): Google Sheets Synchronizer using Service Account credentials. Updates target spr, Authenticate using Service Account JSON and open target worksheet., Locate the 1-indexed row number containing the checkpoint UTR.         Returns t, Filters transactions to only those following the checkpoint UTR,         and bat, SheetsSyncer

### Community 3 - "Community 3"
Cohesion: 0.36
Nodes (8): parse_amount(), parse_date(), parse_record(), parse_reference_name(), parse_to_name(), parse_utr(), Parser module for extracting UPI/Google Pay transaction fields from OCR outputs., TransactionParser

### Community 4 - "Community 4"
Cohesion: 0.22
Nodes (9): 1. End-to-End Execution (Scrape + OCR + Parse + Sync), 2. Individual Pipeline Stages, CLI Commands, code:bash (git clone https://github.com/roshan-pixel/WhatsApp-Web-sessi), code:bash (python main.py run-all --checkpoint-utr 662590373713), code:bash (# Step 1: Scrape active WhatsApp gallery to the right), Installation, Prerequisites (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.39
Nodes (6): CLI Entrypoint for WhatsApp Web Transaction Scraper & Google Sheets Synchronizer, run_all(), run_ocr(), run_parse(), run_scrape(), run_sync()

### Community 6 - "Community 6"
Cohesion: 0.29
Nodes (3): High-performance OCR engine leveraging native Windows WinRT (Windows.Media.Ocr)., Wrapper around Windows 10/11 built-in WinRT OCR API., WinRTOcrEngine

### Community 7 - "Community 7"
Cohesion: 0.40
Nodes (4): code:text (662590373713 // 16 Sept 2026, 1:10 pm // DSR 7 WELLNESS CENT), Detailed Transaction Table, Standard Format (`UTR No // Date // To Banking Name // Amount`), WhatsApp Transaction Report

## Knowledge Gaps
- **17 isolated node(s):** `TransactionParser`, `code:mermaid (flowchart TD)`, `code:mermaid (sequenceDiagram)`, `1. Active Tab Borrowing (Zero Re-authentication)`, `2. Center-Distance Carousel Algorithm` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WebBridgeClient` connect `Community 0` to `Community 8`, `Community 5`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `run_scrape()` connect `Community 5` to `Community 0`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `run_sync()` connect `Community 5` to `Community 2`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **What connects `Configuration settings for WhatsApp Web Scraper and Google Sheets Bot.`, `CLI Entrypoint for WhatsApp Web Transaction Scraper & Google Sheets Synchronizer`, `High-performance OCR engine leveraging native Windows WinRT (Windows.Media.Ocr).` to the rest of the system?**
  _46 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.14736842105263157 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._