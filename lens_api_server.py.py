#!/usr/bin/env python3
"""
Lens Patent API Server with OpenAI Integration
Advanced patent search with LLM-generated queries and self-improvement
"""

from flask import Flask, request, jsonify
import requests
import json
import os
import re
from pathlib import Path

# Load API keys from .env file
ENV_API_KEY = None
OPENAI_API_KEY = None

if Path('.env').exists():
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('LENS_API_KEY='):
                ENV_API_KEY = line.split('=', 1)[1].strip('"\'')
            elif line.startswith('OPENAI_API_KEY='):
                OPENAI_API_KEY = line.split('=', 1)[1].strip('"\'')

if not ENV_API_KEY:
    print("⚠️  WARNING: LENS_API_KEY not found in .env file!")
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not found in .env file!")

app = Flask(__name__)

def validate_boolean_query(query):
    """Basic validation to ensure query has proper boolean structure"""
    if not query:
        return False
    
    # Check for balanced parentheses
    if query.count('(') != query.count(')'):
        return False
    
    return True

def simplify_query(query):
    """Simplify a query by removing excessive parentheses and whitespace"""
    if not query:
        return query
    
    # Remove double parentheses
    while '((' in query:
        query = query.replace('((', '(')
    while '))' in query:
        query = query.replace('))', ')')
    
    # Clean up spaces
    query = re.sub(r'\s+', ' ', query)
    
    return query.strip()

@app.route('/')
def home():
    return r'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lens Patent API Client</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }
            .container { max-width: 1600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
            .header h1 { font-size: 28px; margin-bottom: 8px; }
            .content { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; padding: 30px; }
            .section { display: flex; flex-direction: column; gap: 12px; }
            .section h3 { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #666; margin-top: 16px; }
            label { font-size: 13px; font-weight: 500; color: #333; display: block; margin-bottom: 4px; }
            input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 12px; background: #fafafa; }
            input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; background: white; }
            textarea { resize: vertical; min-height: 100px; }
            .button-row { display: flex; gap: 8px; margin-top: 8px; }
            button { flex: 1; padding: 10px 16px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }
            button:hover { background: #f0f0f0; }
            button.primary { background: #667eea; color: white; border-color: #667eea; }
            button.primary:hover { background: #5568d3; }
            button:disabled { background: #ccc; color: #666; cursor: not-allowed; }
            .status { padding: 10px 12px; border-radius: 6px; font-size: 12px; display: none; margin-top: 8px; }
            .status.show { display: block; }
            .status.error { background: #ffebee; color: #d32f2f; border: 1px solid #ef5350; }
            .status.success { background: #e8f5e9; color: #388e3c; border: 1px solid #81c784; }
            .status.info { background: #e3f2fd; color: #1976d2; border: 1px solid #90caf9; }
            .status.warning { background: #fff3e0; color: #f57c00; border: 1px solid #ffb74d; }
            .response-area { border: 1px solid #ddd; border-radius: 6px; padding: 12px; background: #fafafa; max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 11px; white-space: pre-wrap; word-break: break-word; }
            .full-width { grid-column: 1 / -1; }
            .response-wrapper { grid-column: 1 / -1; margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
            #booleanMode { display: none; }
            .template-btn { padding: 6px 12px; font-size: 11px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; }
            .template-btn:hover { background: #f0f0f0; border-color: #667eea; }
            .result-info { background: #f0f4ff; border-left: 4px solid #667eea; padding: 12px; border-radius: 4px; font-size: 13px; margin: 12px 0; }
            .result-count { font-size: 16px; color: #667eea; font-weight: 600; }
            .column { flex: 1; }
            .column.full { grid-column: 1 / -1; }
            .keyword-badge { display: inline-block; background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin: 2px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Lens Patent API Client with AI</h1>
                <p>Advanced Patent Search - Find patents that describe YOUR invention</p>
            </div>
            <div class="content">
                <!-- LEFT COLUMN: AI QUERY GENERATOR -->
                <div class="column">
                    <div class="section">
                        <h3>Your Invention Description</h3>
                        
                        <label>Describe Your Invention (MOST IMPORTANT)</label>
                        <textarea id="inventionDescription" placeholder="Describe your invention in detail. Focus on:
- What does it do? (function)
- How does it work? (technical mechanism)
- What are its key components? (structure)
- What problem does it solve?

Example: A wearable device that continuously monitors blood pressure using optical sensors and machine learning algorithms to predict cardiovascular events before they occur. The device consists of a wristband with LED arrays that measure blood volume changes, and a processor that analyzes the waveform patterns to detect anomalies." style="min-height: 150px;"></textarea>
                        
                        <label style="margin-top: 12px;">Reference Prior Art (Optional - Helps with terminology)</label>
                        <textarea id="priorArtPatents" placeholder="(Optional) Enter patent IDs that are in the SAME TECHNICAL FIELD. These help the system understand the vocabulary used in this area.&#10;&#10;Separate multiple patents with ;; (double semicolon)&#10;Example: EP4301213 ;; CN121190407 ;; CA3241308&#10;&#10;The system will analyze these to extract relevant technical terminology."></textarea>
                        
                        <div class="button-row">
                            <button onclick="searchPriorArt()" class="primary">Analyze Prior Art Terminology</button>
                            <button onclick="clearPriorArt()">Clear</button>
                        </div>
                        
                        <div id="priorArtSearchStatus" class="status" style="margin-top: 8px;"></div>
                        <div id="priorArtResults" style="margin-top: 12px; padding: 10px; background: #f0f4ff; border-radius: 4px; display: none;">
                            <h4 style="margin-top: 0;">Reference Patents Analyzed:</h4>
                            <div id="priorArtResultsList" style="max-height: 200px; overflow-y: auto;"></div>
                        </div>
                        
                        <div class="button-row">
                            <button onclick="generateQuery()" class="primary">Generate Search Query</button>
                            <button onclick="clearAI()">Clear</button>
                        </div>
                        <div id="aiStatus" class="status"></div>
                        
                        <label style="margin-top: 12px;">Generated Query</label>
                        <textarea id="generatedQuery" placeholder="AI-generated boolean query will appear here..." readonly></textarea>
                        
                        <div id="validationStatus" class="status" style="margin-top: 8px;"></div>
                        <div id="iterationHistory" style="margin-top: 12px; font-size: 11px; color: #666; max-height: 150px; overflow-y: auto;"></div>
                        
                        <div class="button-row">
                            <button onclick="copyGenerated()">Copy Generated</button>
                            <button onclick="useGenerated()">Use This Query</button>
                        </div>
                    </div>
                </div>

                <!-- CENTER COLUMN: MANUAL QUERY BUILDER -->
                <div class="column">
                    <div class="section">
                        <h3>Manual Query Builder</h3>
                        <label>Type</label>
                        <select id="mode" onchange="switchMode()">
                            <option value="boolean">Boolean Query</option>
                        </select>

                        <div id="booleanMode">
                            <label style="margin-top: 12px;">Field(s)</label>
                            <select id="boolField">
                                <option value="all">Title OR Abstract OR Claims</option>
                                <option value="biblio.invention_title">Title Only</option>
                                <option value="abstract">Abstract Only</option>
                                <option value="claims">Claims Only</option>
                            </select>

                            <label style="margin-top: 12px;">Query</label>
                            <textarea id="boolQuery" placeholder="Example: (blood pressure OR cardiovascular) AND (monitoring OR detection) AND (wearable OR device)"></textarea>
                        </div>

                        <label style="margin-top: 12px;">Classification Filters (Optional)</label>
                        <div style="font-size: 11px; color: #666; margin-bottom: 8px;">
                            Add IPC, CPC, or USPC codes to filter results.
                        </div>
                        
                        <label style="font-size: 12px;">IPC Classification (optional)</label>
                        <textarea id="ipcCode" placeholder="e.g., A61B or H02K1/00&#10;Separate multiple codes with ;;" style="min-height: 60px;"></textarea>
                        
                        <label style="font-size: 12px; margin-top: 8px;">CPC Classification (optional)</label>
                        <textarea id="cpcCode" placeholder="e.g., H02K1/00 or A61B5/02&#10;Separate multiple codes with ;;" style="min-height: 60px;"></textarea>

                        <label style="font-size: 12px; margin-top: 8px;">Exclusion Keywords (optional)</label>
                        <textarea id="exclusionKeywords" placeholder="Keywords to EXCLUDE from results&#10;Separate with ;;" style="min-height: 60px;"></textarea>

                        <label style="margin-top: 12px;">Sort (JSON)</label>
                        <textarea id="sort" style="min-height: 60px;">[{"created":"desc"}]</textarea>

                        <div class="button-row" style="margin-top: 12px;">
                            <button onclick="build()" class="primary">Build Request</button>
                            <button onclick="clearAll()">Clear</button>
                        </div>
                        <div id="buildStatus" class="status"></div>
                    </div>
                </div>

                <!-- RIGHT COLUMN: REQUEST & RESULTS -->
                <div class="column">
                    <div class="section">
                        <h3>Request & Execution</h3>
                        
                        <label>Request JSON</label>
                        <textarea id="requestBody" placeholder="Your request will appear here..."></textarea>
                        
                        <div class="button-row">
                            <button onclick="copyReq()">Copy</button>
                            <button onclick="downReq()">Download</button>
                        </div>

                        <label style="margin-top: 12px;">Results Size</label>
                        <input type="number" id="size" value="10" min="1" max="100">

                        <div class="button-row" style="margin-top: 12px;">
                            <button onclick="getCount()" class="primary">Check Count</button>
                        </div>
                        <div id="countStatus" class="status"></div>
                        <div id="countInfo"></div>

                        <div id="retrieveSection" style="display: none; margin-top: 12px;">
                            <div class="button-row">
                                <button onclick="send()" class="primary">Retrieve Results</button>
                                <button onclick="exportHTML()" class="primary" style="background: #28a745;">Export to HTML</button>
                                <button onclick="clearResp()">Clear</button>
                            </div>
                        </div>
                        
                        <div id="sendStatus" class="status" style="margin-top: 12px;"></div>
                        
                        <label style="margin-top: 12px;">Response</label>
                        <div class="response-area" id="response">Ready...</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let bestQuerySoFar = null;
            let bestFoundCount = 0;
            let extractedKeywords = [];

            function switchMode() {
                document.getElementById('booleanMode').style.display = 'block';
            }

            async function searchPriorArt() {
                const priorArtText = document.getElementById('priorArtPatents').value.trim();
                if (!priorArtText) { 
                    alert('Enter at least one patent ID to analyze'); 
                    return; 
                }

                const patentIds = priorArtText.split(';;').map(id => id.trim()).filter(id => id);
                const st = document.getElementById('priorArtSearchStatus');
                const resultsDiv = document.getElementById('priorArtResults');
                const resultsList = document.getElementById('priorArtResultsList');

                st.textContent = `⏳ Analyzing ${patentIds.length} reference patent(s)...`;
                st.className = 'status show info';
                resultsDiv.style.display = 'none';
                resultsList.innerHTML = '';

                try {
                    const res = await fetch('/api/search-prior-art', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({patentIds: patentIds})
                    });

                    const data = await res.json();
                    if (res.ok) {
                        const results = data.results || [];
                        window.identifiedPatents = results;

                        let html = '';
                        let foundCount = 0;
                        let extractedTerms = [];

                        results.forEach((result, idx) => {
                            if (result.found) {
                                foundCount++;
                                html += `<div style="margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #28a745; border-radius: 4px;">
                                    <strong style="color: #28a745;">✅ Patent ${idx + 1}</strong><br>
                                    <strong>ID:</strong> ${result.patentId}<br>
                                    <strong>Title:</strong> ${result.title}<br>
                                    <small style="color: #666;">This patent helps establish technical vocabulary</small>
                                </div>`;
                                
                                // Extract key terms from title
                                const words = result.title.toLowerCase().split(' ');
                                const keyTerms = words.filter(w => w.length > 4 && !['with', 'from', 'this', 'that', 'have', 'are', 'will', 'can', 'may', 'using', 'method', 'system', 'device', 'apparatus'].includes(w));
                                extractedTerms.push(...keyTerms);
                            } else {
                                html += `<div style="margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #dc3545; border-radius: 4px;">
                                    <strong style="color: #dc3545;">❌ Patent ${idx + 1} NOT FOUND</strong><br>
                                    <strong>ID:</strong> ${result.patentId}<br>
                                    <small>Please check the patent ID format</small>
                                </div>`;
                            }
                        });

                        // Display extracted keywords
                        if (extractedTerms.length > 0) {
                            const uniqueTerms = [...new Set(extractedTerms)].slice(0, 15);
                            html += `<div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 4px;">
                                <strong>📝 Extracted Technical Vocabulary:</strong><br>
                                ${uniqueTerms.map(t => `<span class="keyword-badge">${t}</span>`).join(' ')}
                            </div>`;
                            window.extractedKeywords = uniqueTerms;
                        }

                        resultsList.innerHTML = html;
                        resultsDiv.style.display = 'block';

                        if (foundCount > 0) {
                            st.textContent = `✅ Analyzed ${foundCount} reference patent(s). Technical vocabulary extracted.`;
                            st.className = 'status show success';
                        } else {
                            st.textContent = `⚠️ No reference patents found. Please check patent IDs.`;
                            st.className = 'status show warning';
                        }
                    } else {
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    st.textContent = '❌ Search failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function clearPriorArt() {
                document.getElementById('priorArtPatents').value = '';
                document.getElementById('priorArtSearchStatus').textContent = '';
                document.getElementById('priorArtResults').style.display = 'none';
                window.identifiedPatents = [];
                window.extractedKeywords = [];
            }

            async function generateQuery() {
                const inventionDesc = document.getElementById('inventionDescription').value.trim();
                
                if (!inventionDesc) { 
                    alert('Please describe your invention first'); 
                    return; 
                }

                const st = document.getElementById('aiStatus');
                const vs = document.getElementById('validationStatus');
                const historyDiv = document.getElementById('iterationHistory');
                
                st.textContent = '⏳ Analyzing your invention and generating search query...';
                st.className = 'status show info';
                vs.textContent = '';
                historyDiv.innerHTML = '';
                bestQuerySoFar = null;
                bestFoundCount = 0;

                try {
                    // Get prior art titles if available
                    let priorArtTitles = '';
                    if (window.identifiedPatents && window.identifiedPatents.length > 0) {
                        const foundPatents = window.identifiedPatents.filter(p => p.found);
                        if (foundPatents.length > 0) {
                            priorArtTitles = '\n\nREFERENCE PATENTS (for vocabulary reference):\n';
                            foundPatents.forEach((patent, idx) => {
                                priorArtTitles += `${idx + 1}. ${patent.title}\n`;
                            });
                        }
                    }

                    const res = await fetch('/api/generate-query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            invention: inventionDesc,
                            priorArtTitles: priorArtTitles,
                            extractedKeywords: window.extractedKeywords || []
                        })
                    });

                    const data = await res.json();
                    if (res.ok) {
                        document.getElementById('generatedQuery').value = data.query;
                        st.textContent = '✅ Search query generated!';
                        st.className = 'status show success';
                        
                        // Show extracted keywords
                        if (data.keywords && data.keywords.length > 0) {
                            const keywordHtml = `<div style="margin-top: 8px; padding: 8px; background: #f0f4ff; border-radius: 4px;">
                                <strong>🔑 Key concepts identified:</strong><br>
                                ${data.keywords.map(k => `<span class="keyword-badge">${k}</span>`).join(' ')}
                            </div>`;
                            vs.innerHTML = keywordHtml;
                        }
                    } else {
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    st.textContent = '❌ Failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function useGenerated() {
                const q = document.getElementById('generatedQuery').value.trim();
                if (!q) { alert('Generate a query first'); return; }
                
                document.getElementById('mode').value = 'boolean';
                document.getElementById('boolField').value = 'all';
                document.getElementById('boolQuery').value = q;
                switchMode();
                build();
            }

            function copyGenerated() {
                const q = document.getElementById('generatedQuery').value;
                if (!q) return alert('Generate query first');
                navigator.clipboard.writeText(q);
            }

            function clearAI() {
                document.getElementById('inventionDescription').value = '';
                document.getElementById('priorArtPatents').value = '';
                document.getElementById('generatedQuery').value = '';
                document.getElementById('aiStatus').textContent = '';
                document.getElementById('validationStatus').textContent = '';
                document.getElementById('iterationHistory').innerHTML = '';
                window.identifiedPatents = [];
                window.extractedKeywords = [];
                bestQuerySoFar = null;
                bestFoundCount = 0;
            }

            function parseQuery(tokens, field) {
                let pos = 0;
                const peek = () => tokens[pos];
                const take = () => tokens[pos++];

                const parseOr = () => {
                    let l = parseAnd();
                    while (peek() === 'OR') {
                        take();
                        const r = parseAnd();
                        l = {bool: {should: [l, r], minimum_should_match: 1}};
                    }
                    return l;
                };

                const parseAnd = () => {
                    let l = parseNot();
                    while (peek() === 'AND') {
                        take();
                        const r = parseNot();
                        if (l.bool && l.bool.must) {
                            l.bool.must.push(r);
                        } else {
                            l = {bool: {must: [l, r]}};
                        }
                    }
                    return l;
                };

                const parseNot = () => {
                    if (peek() === 'NOT') {
                        take();
                        return {bool: {must_not: [parsePrim()]}};
                    }
                    return parsePrim();
                };

                const parsePrim = () => {
                    if (peek() === '(') {
                        take();
                        const e = parseOr();
                        take();
                        return e;
                    }
                    return makeTerm(take(), field);
                };

                const makeTerm = (t, f) => {
                    if (!t) throw new Error('Unexpected end');
                    const m = t.match(/^"(.+?)"~(\d+)$/);
                    if (m) return {match_phrase: {[f]: {query: m[1], slop: parseInt(m[2])}}};
                    if (t.startsWith('"') && t.endsWith('"')) return {match_phrase: {[f]: t.slice(1, -1)}};
                    if (t.includes('*') || t.includes('?')) return {wildcard: {[f]: {value: t.toLowerCase()}}};
                    return {match: {[f]: t}};
                };

                return parseOr();
            }

            function tokenize(s) {
                let tokens = [], cur = '', inQ = false;
                for (let i = 0; i < s.length; i++) {
                    const c = s[i];
                    if (c === '"') { inQ = !inQ; cur += c; }
                    else if (inQ) { cur += c; }
                    else if ('()'.includes(c)) { if (cur.trim()) tokens.push(cur.trim()); tokens.push(c); cur = ''; }
                    else if (c === ' ') { if (cur.trim()) tokens.push(cur.trim()); cur = ''; }
                    else { cur += c; }
                }
                if (cur.trim()) tokens.push(cur.trim());
                return tokens;
            }

            function build() {
                try {
                    const qstr = document.getElementById('boolQuery').value.trim();
                    const fieldOpt = document.getElementById('boolField').value;
                    if (!qstr) throw new Error('Enter query');
                    const toks = tokenize(qstr);
                    
                    let q = {};
                    if (fieldOpt === 'all') {
                        const fields = ['biblio.invention_title', 'abstract', 'claims'];
                        const queries = fields.map(f => parseQuery(toks.slice(), f));
                        q = {bool: {should: queries, minimum_should_match: 1}};
                    } else {
                        q = parseQuery(toks, fieldOpt);
                    }

                    const sz = parseInt(document.getElementById('size').value) || 10;
                    const so = JSON.parse(document.getElementById('sort').value);
                    
                    const ipcInput = document.getElementById('ipcCode').value.trim();
                    const cpcInput = document.getElementById('cpcCode').value.trim();
                    const exclusionInput = document.getElementById('exclusionKeywords').value.trim();
                    
                    const ipcCodes = ipcInput ? ipcInput.split(';;').map(c => c.trim()).filter(c => c) : [];
                    const cpcCodes = cpcInput ? cpcInput.split(';;').map(c => c.trim()).filter(c => c) : [];
                    const exclusionKeywords = exclusionInput ? exclusionInput.split(';;').map(c => c.trim()).filter(c => c) : [];
                    
                    let req = {
                        query: q,
                        size: sz,
                        from: 0,
                        _source: {
                            includes: ['lens_id', 'biblio.invention_title', 'legal_status', 'abstract', 'claims', 'biblio.classifications_ipc', 'biblio.classifications_cpc']
                        },
                        sort: so
                    };
                    
                    let mustNotClauses = [];
                    exclusionKeywords.forEach(keyword => {
                        mustNotClauses.push({match: {'biblio.invention_title': keyword}});
                        mustNotClauses.push({match: {'abstract': keyword}});
                        mustNotClauses.push({match: {'claims': keyword}});
                    });
                    
                    if (ipcCodes.length > 0 || cpcCodes.length > 0) {
                        let queryParts = [];
                        ipcCodes.forEach(code => { queryParts.push('class_ipcr.symbol:' + code + '*'); });
                        cpcCodes.forEach(code => { queryParts.push('class_cpc.symbol:' + code + '*'); });
                        
                        const filterQuery = queryParts.join(' OR ');
                        if (filterQuery) {
                            req.query = { bool: { must: [q], filter: { query_string: { query: filterQuery } } } };
                            if (mustNotClauses.length > 0) req.query.bool.must_not = mustNotClauses;
                        }
                    } else if (mustNotClauses.length > 0) {
                        req.query = { bool: { must: [q], must_not: mustNotClauses } };
                    }

                    document.getElementById('requestBody').value = JSON.stringify(req, null, 2);
                    const s = document.getElementById('buildStatus');
                    s.textContent = '✅ Request built. Check count next.';
                    s.className = 'status show success';
                    
                    document.getElementById('countInfo').innerHTML = '';
                    document.getElementById('retrieveSection').style.display = 'none';
                } catch (e) {
                    const s = document.getElementById('buildStatus');
                    s.textContent = '❌ ' + e.message;
                    s.className = 'status show error';
                }
            }

            async function getCount() {
                const r = document.getElementById('requestBody').value.trim();
                if (!r) { alert('Build request first'); return; }

                const st = document.getElementById('countStatus');
                st.textContent = '⏳ Counting...';
                st.className = 'status show info';

                try {
                    const res = await fetch('/api/count', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({request: JSON.parse(r)})
                    });

                    const data = await res.json();
                    if (res.ok) {
                        const total = data.total;
                        const resultSize = parseInt(document.getElementById('size').value) || 10;
                        
                        let infoHtml = `<div class="result-info">
                            <strong>Total: <span class="result-count">${total.toLocaleString()}</span></strong>
                            Retrieving ${Math.min(resultSize, total)} results
                        </div>`;
                        
                        document.getElementById('countInfo').innerHTML = infoHtml;
                        document.getElementById('retrieveSection').style.display = 'block';
                        st.textContent = `✅ Found ${total.toLocaleString()}`;
                        st.className = 'status show success';
                    } else {
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    st.textContent = '❌ Failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function copyReq() {
                const r = document.getElementById('requestBody').value;
                if (!r) return alert('Build first');
                navigator.clipboard.writeText(r);
            }

            function downReq() {
                const r = document.getElementById('requestBody').value;
                if (!r) return alert('Build first');
                const b = new Blob([r], {type: 'application/json'});
                const u = URL.createObjectURL(b);
                const a = document.createElement('a');
                a.href = u;
                a.download = 'lens_request.json';
                a.click();
            }

            function clearAll() {
                document.getElementById('boolQuery').value = '';
                document.getElementById('requestBody').value = '';
                document.getElementById('countInfo').innerHTML = '';
                document.getElementById('retrieveSection').style.display = 'none';
            }

            function clearResp() {
                document.getElementById('response').textContent = 'Ready...';
            }

            async function send() {
                const r = document.getElementById('requestBody').value.trim();
                if (!r) { alert('Build first'); return; }

                const resp = document.getElementById('response');
                resp.textContent = 'Retrieving...';
                const st = document.getElementById('sendStatus');
                st.textContent = '⏳ Retrieving...';
                st.className = 'status show info';

                try {
                    const res = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({request: JSON.parse(r)})
                    });

                    const data = await res.json();
                    if (res.ok) {
                        resp.textContent = JSON.stringify(data.response, null, 2);
                        const c = data.response?.data?.length || 0;
                        st.textContent = `✅ Retrieved ${c} results`;
                        st.className = 'status show success';
                    } else {
                        resp.textContent = JSON.stringify(data, null, 2);
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    resp.textContent = 'Error: ' + e.message;
                    st.textContent = '❌ Failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function exportHTML() {
                const responseText = document.getElementById('response').textContent;
                if (!responseText || responseText === 'Ready...') { alert('No results to export'); return; }
                
                try {
                    const data = JSON.parse(responseText);
                    const patents = data.data || [];
                    
                    let html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Patent Search Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .patent { margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; background: #f9f9f9; }
        .patent h3 { margin: 0 0 10px 0; color: #667eea; }
        .field { margin: 8px 0; }
        .label { font-weight: bold; color: #666; }
        .value { color: #333; margin-left: 10px; }
        .classifications { background: #f0f4ff; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Patent Search Results</h1>
        <p>Total Results: <strong>${patents.length}</strong></p>
        <hr>
`;
                    
                    patents.forEach((patent, index) => {
                        const title = patent.biblio?.invention_title?.[0]?.text || 'N/A';
                        const abstract = patent.abstract?.[0]?.text || 'N/A';
                        const lensId = patent.lens_id || 'N/A';
                        
                        html += `
        <div class="patent">
            <h3>${index + 1}. ${title}</h3>
            <div class="field">
                <span class="label">Lens ID:</span>
                <span class="value">${lensId}</span>
            </div>
            <div class="field">
                <span class="label">Abstract:</span>
                <div class="value">${abstract.substring(0, 300)}${abstract.length > 300 ? '...' : ''}</div>
            </div>
        </div>
`;
                    });
                    
                    html += `</div></body></html>`;
                    const blob = new Blob([html], {type: 'text/html'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'patent_results_' + new Date().toISOString().slice(0,10) + '.html';
                    a.click();
                } catch (e) {
                    alert('Error exporting: ' + e.message);
                }
            }

            window.onload = () => { 
                switchMode(); 
                build();
            };
        </script>
    </body>
    </html>
    '''

@app.route('/api/get-patent-details', methods=['POST'])
def get_patent_details():
    """Fetch full patent details by Lens ID"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        lens_ids = data.get('lensIds', [])

        if not lens_ids:
            return jsonify({'error': 'No Lens IDs provided'}), 400

        import time
        results = []
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}

        for idx, lens_id in enumerate(lens_ids):
            if idx > 0:
                time.sleep(0.3)
            
            search_request = {
                "query": {"match": {"lens_id": lens_id}},
                "size": 1,
                "from": 0,
                "_source": {"includes": ["lens_id", "biblio.invention_title", "abstract"]}
            }

            try:
                response = requests.post('https://api.lens.org/patent/search', json=search_request, headers=headers, timeout=30)

                if response.status_code == 200:
                    response_data = response.json()
                    patents = response_data.get('data', [])

                    if patents:
                        patent = patents[0]
                        title = patent.get('biblio', {}).get('invention_title', [{}])[0].get('text', '') if isinstance(patent.get('biblio', {}).get('invention_title'), list) else ''
                        abstract = patent.get('abstract', [{}])[0].get('text', '') if isinstance(patent.get('abstract'), list) else ''
                        
                        results.append({'lens_id': lens_id, 'title': title, 'abstract': abstract, 'found': True})
                    else:
                        results.append({'lens_id': lens_id, 'found': False})
                else:
                    results.append({'lens_id': lens_id, 'found': False})
            except:
                results.append({'lens_id': lens_id, 'found': False})

        return jsonify({'results': results}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-prior-art', methods=['POST'])
def search_prior_art():
    """Search Lens database to identify patents by their IDs"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        patent_ids = data.get('patentIds', [])

        if not patent_ids:
            return jsonify({'error': 'No patent IDs provided'}), 400

        import time
        results = []
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}

        for idx, patent_id in enumerate(patent_ids):
            if idx > 0:
                time.sleep(0.5)
            
            search_request = {
                "query": {"match": {"ids": patent_id}},
                "size": 1,
                "from": 0,
                "_source": {"includes": ["lens_id", "country", "doc_number", "kind", "biblio.invention_title"]}
            }

            try:
                response = requests.post('https://api.lens.org/patent/search', json=search_request, headers=headers, timeout=30)

                if response.status_code == 200:
                    response_data = response.json()
                    patents = response_data.get('data', [])
                    
                    if patents:
                        patent = patents[0]
                        results.append({
                            'found': True,
                            'patentId': patent_id,
                            'lens_id': patent.get('lens_id', 'N/A'),
                            'title': patent.get('biblio', {}).get('invention_title', [{}])[0].get('text', 'N/A') if isinstance(patent.get('biblio', {}).get('invention_title'), list) else 'N/A',
                            'country': patent.get('country', 'N/A'),
                            'doc_number': patent.get('doc_number', 'N/A'),
                            'kind': patent.get('kind', 'N/A')
                        })
                    else:
                        results.append({'found': False, 'patentId': patent_id})
                else:
                    results.append({'found': False, 'patentId': patent_id})
            except:
                results.append({'found': False, 'patentId': patent_id})

        return jsonify({'results': results}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-query', methods=['POST'])
def generate_query():
    """Generate a boolean search query based on invention description and prior art terminology"""
    try:
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 400

        data = request.get_json() or {}
        invention = data.get('invention', '').strip()
        prior_art_titles = data.get('priorArtTitles', '').strip()
        extracted_keywords = data.get('extractedKeywords', [])

        if not invention:
            return jsonify({'error': 'No invention description provided'}), 400

        system_prompt = """You are a patent search specialist. Your task is to create a boolean search query that will find patents describing a specific invention.

CRITICAL PRINCIPLE:
- The INVENTION DESCRIPTION is the PRIMARY source for what to search for
- Reference patents (if provided) help you understand the TECHNICAL VOCABULARY used in this field
- The goal is to find patents that describe the INVENTION, not just the reference patents

QUERY STRUCTURE RULES:
1. Use groups: (term1 OR term2) AND (term3 OR term4) AND (term5 OR term6)
2. Each group represents a key CONCEPT from your invention
3. NEVER use AND inside parentheses - only OR inside groups
4. 2-3 groups maximum - keep it focused
5. Use word* for variations when appropriate (e.g., monitor* for monitor, monitoring, monitored)

HOW TO BUILD THE QUERY:
1. Read the invention description carefully
2. Identify 2-3 key concepts (what it does, how it works, what it's made of)
3. For each concept, list 2-3 synonyms or related terms
4. If reference patents are provided, check if they use specific terminology for these concepts
5. Format as: (synonym1 OR synonym2) AND (term3 OR term4)

EXAMPLE:
Invention: "A wearable device that continuously monitors blood pressure using optical sensors"
Query: (wearable OR wristband OR portable) AND (blood pressure OR cardiovascular OR hypertension) AND (monitor* OR detect* OR sensor*)

Output ONLY the query string, nothing else."""

        user_message = f"""INVENTION DESCRIPTION (PRIMARY SOURCE):
{invention}

"""
        if prior_art_titles:
            user_message += f"""REFERENCE PATENTS (for technical vocabulary reference):
{prior_art_titles}

"""
        if extracted_keywords:
            user_message += f"""EXTRACTED TECHNICAL VOCABULARY from reference patents:
{', '.join(extracted_keywords[:15])}

"""
        
        user_message += """TASK: Create a boolean query to find patents that describe this invention.
Focus on the key concepts from the invention description.
Use the technical vocabulary from reference patents to inform your term selection.
Output ONLY the query."""

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
            json={
                'model': 'gpt-4o',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                'temperature': 0.2,
                'max_tokens': 400
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            query = result['choices'][0]['message']['content'].strip()
            query = simplify_query(query)
            
            # Extract keywords from the invention description for display
            words = re.findall(r'\b[a-zA-Z]{4,}\b', invention.lower())
            stopwords = {'with', 'from', 'this', 'that', 'have', 'are', 'will', 'can', 'may', 'using', 'method', 'system', 'device', 'apparatus', 'invention', 'described'}
            keywords = list(set([w for w in words if w not in stopwords]))[:10]
            
            print(f"\n=== Generated Query ===")
            print(f"Query: {query}")
            print(f"Key concepts: {keywords}")
            
            return jsonify({'query': query, 'keywords': keywords}), 200
        else:
            return jsonify({'error': f'OpenAI error: {response.status_code}'}), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/count', methods=['POST'])
def count():
    """Count total matching results"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        search_request = data.get('request')

        if not search_request:
            return jsonify({'error': 'Request required'}), 400

        count_request = {
            'query': search_request.get('query'),
            'size': 0
        }

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}
        response = requests.post('https://api.lens.org/patent/search', json=count_request, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            total = result.get('total', 0)
            return jsonify({'total': total}), 200
        else:
            return jsonify({'error': f'API error {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Retrieve actual results"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        search_request = data.get('request')

        if not search_request:
            return jsonify({'error': 'Request required'}), 400

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}
        response = requests.post('https://api.lens.org/patent/search', json=search_request, headers=headers, timeout=30)

        if response.status_code == 200:
            return jsonify({'response': response.json()}), 200
        else:
            return jsonify({'error': f'API error {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    status = "✅ Both APIs configured" if (ENV_API_KEY and OPENAI_API_KEY) else "⚠️  Check .env file"
    print(f"\n🚀 Lens Patent API Client with AI\n📍 http://localhost:5000\n{status}\n")
    print("💡 TIP: The system prioritizes your INVENTION DESCRIPTION")
    print("   Reference patents are used ONLY for technical vocabulary")
    print("   This ensures results are relevant to YOUR invention\n")
    app.run(debug=False, host='127.0.0.1', port=5000)