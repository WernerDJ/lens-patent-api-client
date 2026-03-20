# Lens Patent API Client

A powerful web-based patent search tool that leverages the Lens Patent API with advanced boolean query building, AI-powered query generation, and result filtering capabilities.

## Overview

This application provides an intuitive interface to search patents using the Lens Patent API, featuring:

- **Boolean Query Builder** - Create complex search queries with AND, OR, NOT operators across Title, Abstract, and Claims fields
- **AI-Powered Query Generation** - Automatically generate optimal search strategies from patent abstracts using OpenAI
- **Classification Filtering** - Filter results by IPC and CPC patent classifications
- **Exclusion Keywords** - Exclude unwanted terms from your search results
- **Result Export** - Download patent search results as formatted HTML files
- **Multi-Field Search** - Search simultaneously across patent titles, abstracts, and claims

## Prerequisites

Before getting started, please read the **[Lens Patent API Documentation](https://github.com/cambialens/lens-api-doc/tree/master)** to understand:
- API endpoints and request format
- Available search fields and classification systems
- Query syntax and boolean operators
- Rate limits and best practices

This documentation will help you understand how to customize queries and make the most of this tool.

## Installation

### Requirements
- Python 3.8+
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd lens-patent-api-client
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file**
   ```bash
   cp .env.example .env
   ```

4. **Configure API keys**
   Edit `.env` and add your API keys:
   ```
   LENS_API_KEY=your_lens_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   - **Lens API Key**: Get from [Lens.org API](https://www.lens.org/settings/api)
   - **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

5. **Run the server**
   ```bash
   python lens_api_server.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Quick Start Example

This example demonstrates searching for patents related to AI-powered blood pressure monitoring systems.

### Example Patents

These three patents make a good example for testing the application:

1. **CN121190407** - Chinese patent on AI-based neurovascular monitoring
   - Link: https://patents.google.com/patent/CN121190407A/en?oq=CN121190407
   - Key features: Artificial intelligence, blood vessel monitoring, real-time analysis

2. **EP4301213** - European patent on stroke risk prediction system
   - Link: https://patents.google.com/patent/EP4301213A1/en?oq=+EP4301213
   - Key features: Blood pressure analysis, artificial intelligence, biomechanical monitoring

3. **CA3241308** - Canadian patent on medical device monitoring
   - Link: https://patents.google.com/patent/CA3241308A1/en?oq=+CA3241308
   - Key features: Monitoring devices, artificial intelligence, medical applications

### Workflow

1. **Generate Query from Abstracts**
   - Copy the abstract text from each patent
   - Paste into "Patent Abstracts" field, separated by `;;` (double semicolon)
   - Click "Generate Query from Abstracts"
   - AI will create something like: `(monitoring OR controlling OR analyzing) AND ("blood pressure" OR "blood vessel") AND ("artificial intelligence" OR "machine learning")`

2. **Build and Filter**
   - Select "Title OR Abstract OR Claims" as the search field
   - Add IPC/CPC codes: `A61B5* ;; G06N*` (medical and AI classifications)
   - Add exclusion keywords: `imaging ;; diabetes ;; glucose`
   - Click "Build Request"

3. **Search**
   - Click "Check Count" to see total matching results
   - Set "Results Size" to anything else than 10, by default, and  click again "Build Request"
   - Click "Retrieve Results"

4. **Export**
   - Click "Export to HTML" to download results as an HTML file
   - Results include:
     - Patent titles
     - Lens IDs and legal status
     - IPC and CPC classifications
     - Abstracts

## Features

### Boolean Query Builder

Create complex queries using boolean operators:

```
(monitoring OR controlling OR analyzing) AND 
("blood pressure" OR "blood vessel") AND 
("artificial intelligence" OR "machine learning") NOT 
(imaging OR diabetes)
```

**Supported operators:**
- `AND` - Both terms must be present
- `OR` - Either term must be present
- `NOT` - Term must not be present
- `()` - Group terms for precedence
- `"phrase"~2` - Proximity (within 2 words)
- `word*` - Wildcards (word, words, wording, etc.)

### AI Query Generation

Automatically generate optimal search queries:
1. Paste 2-3 patent abstracts separated by `;;`
2. Click "Generate Query from Abstracts"
3. AI extracts functional, structural, and technical keywords
4. Creates balanced boolean query

### Classification Filtering

Filter by IPC (International Patent Classification) or CPC (Cooperative Patent Classification):

- **IPC Code Format**: `A61B`, `A61B5*`, `H02K`
- **CPC Code Format**: `H02K1/00`, `A61B5/02`
- **Multiple codes**: Separate with `;;` to filter by any classification

### Exclusion Keywords

Exclude unwanted results without affecting the main query:
- Enter keywords separated by `;;`
- Example: `imaging ;; diabetes ;; glucose`
- Filters from title, abstract, and claims automatically

### Result Export

Download patent results as a formatted HTML file:
- Filename: `patent_results_YYYY-MM-DD.html`
- Includes: Titles, classifications, abstracts, status, Lens IDs


