---
name: openagent-search-agent
description: Use when the user asks to find, recommend, or select Agents with an explicit query, browse available Agents without a query, or an upstream business Skill requests headless capability discovery. Perform one discovery and selection protocol only; do not plan tasks, search again, or call execution tools.
---

# OpenAgent Agent Discovery

## Muse Host Adaptation

Use the tool names and schemas actually exposed by the current Muse connection, and follow [Muse Host Boundary](../openagent-run-agent/SKILL.md#muse-host-boundary) for secure authentication. Open the browser, wait, and clean up within the Host capability boundaries in this document; do not assume fixed tool names, runtime directories, or component APIs.

## Purpose

Complete a single OpenAgent discovery request. Direct user searches open the available Muse browser or provide the selection-page link, then wait for a trusted user selection, with or without an explicit query. Background searches return complete candidates to the caller. This Skill does not plan business tasks, automatically search again, or call Agent execution tools.

## Terminology

- **OpenAgent**: The platform and tools for discovering, invoking, and managing Remote Agents.
- **Remote Agent**: A remote service callable through OpenAgent; it does not automatically inherit the Host conversation or local environment.

## Status Update Format

When entering a workflow stage, send a standalone user-visible progress message in Muse using the following format; do not place it in reasoning or tool logs:

```text
OpenAgent: <stage name> — <brief action phrase>
```

- Use the exact English workflow-stage heading for `<stage name>` and a short, verb-led action phrase in the user's language. Describe only the current action, without reasoning, results, next steps, candidate counts, internal identifiers, or handoff URLs; never claim success before authoritative confirmation.
- Emit one update on stage entry. Do not repeat it for tool polling, candidate-by-candidate checks, or resuming a pending call; re-entry may emit a new update.
- Deliver actual results separately. `Output` and `Next` describe internal data handoff and workflow transitions; do not display these labels to the user.
- For an upstream `presentation_mode=headless` request, suppress all user-facing stage updates, candidate-check notices, and UI; return data only to the caller, which owns progress reporting. On cancellation, go directly to Failure Handling and output only its fixed terminal reply, without another stage update.

## Workflow

1. Run `Agent Search` once. Every direct user search uses browser presentation, with or without an explicit query; an upstream headless request uses headless presentation.
2. Pass a browser handoff result to `Browser Handoff` for validation and opening. Pass headless results to `Result Validation and Delivery`.
3. After `Browser Handoff` opens, recovers, or links the page, immediately enter `Agent Selection` in the same Turn. Use the shared Wait and Close Orchestration for every wait. On `more_requested`, return to `Browser Handoff` with the new URL, then resume selection on the same session.
4. Pass a successful selection to `Result Validation and Delivery` in the same Turn for authorization validation and handoff to `openagent-run-agent`. Handle cancellation, timeout, invalid results, or other failures in `Failure Handling` and end locally.

### Loop Control

Call the search tool only once per discovery request. For `more_requested`, use only the new handoff URL returned by the wait result and continue waiting on the same selection session; do not start a new search. The caller decides whether to search again. Keep only one active wait per selection session at a time.

## Workflow Stages

Follow the orchestration in Workflow and transition only through each stage's `Next` contract.

### Agent Search

Input is an explicit query with constraints, a general browsing intent, or a headless request from an upstream business Skill. Emit the stage update before searching, except in headless mode.

1. For every direct user search, with or without an explicit query, call `openagent_search(presentation_mode=browser)` once with `locale=zh-CN|en-US` matching the current user's language and a new stable `idempotency_key`. Pass explicit search terms as `q` (1–200 Unicode characters) to prefill and search the page, preserving names and constraints. Otherwise omit `q`; never invent terms. Do not pass other search filters. Retain the original request for post-selection handoff. Do not call `openagent_user_guide`.
2. For an upstream headless request, call `openagent_search` once with the supplied query, `presentation_mode=headless`, and the same locale rule; preserve the caller's query and constraints. In this mode, pass category, tags, sort, and pagination only when explicitly requested. Pass `category` only when the caller explicitly supplies a server-recognized category ID; never put natural-language search terms directly in that field.
3. Preserve the returned candidates and metadata without selecting, reordering, or inventing Agents. Do not open a browser or call `openagent_wait_for_selection` in this stage.

| Request source | `presentation_mode` | Result handling |
| --- | --- | --- |
| An upstream business Skill requests background capability discovery | `headless` | Do not display a Widget or the available Muse browser; return structured candidates only to the current caller |
| The user searches or browses available Agents, with or without an explicit query | `browser` | Do not show the Search Agents Widget; pass the returned handoff result to Browser Handoff, open the available Muse browser, and wait for selection |

“Find a PPT Agent”, “Find a stock analysis Agent”, “What is available in OpenAgent?”, and “Browse available Agents” all use `presentation_mode=browser` and open the Muse discovery page.

**Output:** One unchanged search Tool Result, including candidates and any presentation or selection metadata.

**Next:** Browser results enter `Browser Handoff`; headless results enter `Result Validation and Delivery`; errors or inconsistent presentation metadata enter `Failure Handling`.

### Browser Handoff

Input is the browser result from Agent Search or a trusted `more_requested` result from Agent Selection. This stage opens the page; it does not search or wait for selection.

1. For an initial browser result, require `presentation_mode=browser`, `browser_handoff=true`, `status=pending`, non-empty `selection_id` and `handoff_url`, and no Search Agents Widget binding. For `more_requested`, require the same trusted selection session and a new non-empty `handoff_url` from its wait result. Reject invalid handoffs before opening a page.
2. Use only the original absolute HTTPS `handoff_url` and trusted `selection_id` from that Tool Result. Do not compose or rewrite the URL, or reuse one from another selection session. Use the full URL only as the current flow's navigation argument or the target of its localized “打开 OpenAgent 选择页”/“Open OpenAgent selection page” link; do not additionally output bare URLs, short-lived tokens, or logs.
3. Emit the Browser Handoff update. If Muse actually provides a browser-opening tool, open the selection page once in a new tab using its actual schema. If tab queries are supported, record existing tabs first and retain the trusted handle of the tab created in this flow. Preserve existing tabs without navigating over existing pages; do not assume a right-side panel or fixed API. If the opening tool is missing, fails, or times out, preserve the original URL as an “Open OpenAgent selection page” link in the user's language, without claiming that automatic opening succeeded.
4. After an opening failure or timeout, check once only if an actual tab-query tool exists. Reuse an opened target only when its ownership by the current flow is confirmed. Without trusted ownership or a display receipt, keep the link and explain that automatic opening is unconfirmed; do not navigate again. After handing off the link, immediately wait for the same selection session; do not require page loading to finish before waiting.
5. For `more_requested`, hand off only the new URL returned by the same selection session under the rules above. After successfully handing off the new page, attempt to close only the replaced old selection tab confirmed to have been created in this flow. Do not close the new page, pre-existing tabs, or result pages. If closing capabilities or handles are missing, preserve the actual state without repeatedly reopening pages.

**Output:** The same trusted selection session and the opened, recovered, or linked handoff page, or an invalid handoff.

**Next:** Immediately enter `Agent Selection` in the same Turn after opening, recovery, or link delivery. Page load state must not be a prerequisite for listening or handling a terminal selection state. Invalid handoffs enter `Failure Handling`; unavailable automatic opening uses the link handoff above.

### Agent Selection

Input is a successfully opened, recovered, or linked Browser Handoff with a non-empty `selection_id` for the same session. Headless results and results without a selection handle must not enter this stage.

1. The discovery page is already opened, recovered, or linked. Regardless of whether the original request was to search, recommend, view, select, or find and run, emit the Agent Selection update and immediately use `selection_id` to call `openagent_wait_for_selection` through Wait and Close Orchestration in the same Turn. Do not deliver candidates first, end the Turn to await a new user message, or open the available Muse browser again.
2. Allow only one active wait call per `selection_id` at a time. The selection-wait update replaces the opening status; do not append another guidance message or repeat the update when resuming a pending orchestration call.
3. On `more_requested`, retain the same selection session and pass only the newly returned `handoff_url` to Browser Handoff. Do not search again or start a second simultaneous wait.
4. On `selected`, `cancelled`, or `timed_out`, Wait and Close Orchestration attempts terminal cleanup once before returning the original result. Do not close again in subsequent stages. This stage does not validate execution authorization or invoke an Agent.

**Output:** The unchanged trusted wait result from the same selection session, with terminal cleanup already attempted when applicable.

**Next:** `more_requested` returns to `Browser Handoff`; `selected` enters `Result Validation and Delivery` in the current Turn; cancellation, timeout, or wait failure enters `Failure Handling`. Do not end the Turn between the successful wait and authorization handoff.

### Result Validation and Delivery

Input is a complete headless search result or a trusted terminal selection state. Emit the Result Validation and Delivery update except for headless requests. Validate before delivering candidates or handing off authorization.

- If `recommended_agent_id` is non-empty, `results` must contain exactly one matching candidate with a non-empty name. On mismatch, do not recommend or execute an Agent; enter Failure Handling. For headless requests, return the current query and trusted public error; for direct requests, explain that search results are temporarily unavailable and end.
- Determine whether candidates are empty only from `results` and trusted counts, not from a missing selection handle. Headless results may contain multiple candidates without a handle. Do not show an empty card or invent Agents.
- For a direct `search_only` request, complete the browser handoff and `openagent_wait_for_selection` in the same Turn first. After successful selection, enter the No Explicit Intent branch of `openagent-run-agent`; do not end the Turn early because the original request was only to search or select.
- `find_and_run` still returns only structured discovery results. The current caller decides whether to search again or execute. For direct user requests, hand off to `openagent-run-agent` only when an explicit executable prompt and trusted authorization already exist.
- Headless search returns complete model-readable candidates only. It creates no selection session, returns no Widget binding metadata, and does not enter the human-assisted discovery chain. The current caller selects a trusted Agent.
- Return headless search results completely unchanged to the current caller. Do not rewrite candidates, reorder results, or replace the upstream decision.
- For `status=selected`, terminal cleanup has already been attempted; do not close again. Read only trusted `selected_agent`, `execution_authorization`, and `action`, preserving `selected_agent.name` and the Agent Card's `selected_agent.description`. A selection action provides server authorization only; it does not replace the user's business requirement. A general discovery request has no executable task. If the original request only searches, recommends, views, or selects an Agent, pass the trusted Agent to the No Explicit Intent branch of `openagent-run-agent` for its fixed two-line guidance. Do not use the selection action or an Agent default task to start a run; do not execute a default task.
- Normal public discovery returns `execution_authorization=null` and `action.type=none`. Validate the trusted `selected_agent` identity, then pass it with the user's original business requirement to `openagent-run-agent` using ordinary `agent_id` and `data`. If no business task was supplied, use its No Explicit Intent branch. A selected Agent is not authorization to invent a task.
- Only a legacy persisted trial selection may contain `execution_authorization.source=user_selection`, `immediate=true`, and `action.type=call_tool`. Validate its matching selection handle and bound idempotency key before handing it to the execution Skill; never reinterpret an invalid legacy authorization as an ordinary task. After validation, read the `openagent-run-agent` Skill if needed, or reuse it if already read in the current context. Immediately pass the selection result and authorization unchanged to `openagent-run-agent` in the same Turn. Do not end the Turn between `openagent_wait_for_selection` and `openagent-run-agent`.

**Output:** Complete candidate results, or validated and unchanged user selection authorization with the Selected Remote Agent.

**Next:** For headless requests, deliver results to the caller and end. With valid authorization, hand off to `openagent-run-agent` in the same Turn so it can determine whether an executable business requirement exists.

### Failure Handling

Input is a trusted failure result from search, selection waiting, handoff, or result validation. Emit the Failure Handling update except for headless requests and cancellation.

For cancellation replies, set `display_locale` to `zh-CN` or `en-US`: explicit user preference > trusted Host/caller locale > request/conversation language > `en-US`. Ignore code, quotes, Tool output, and fixed installation/selection prompts. Output only the matching single-language reply.

- For `status=cancelled`, terminal cleanup has already been attempted by Wait and Close Orchestration. Do not close again or emit a stage update. Use only existing trusted evidence of page closure; `status=cancelled` alone does not prove that the page is closed. If closure is confirmed, output only “你已关闭 OpenAgent 发现页。” for `zh-CN` or “You have closed the OpenAgent discovery page.” for `en-US`. Otherwise, output only “OpenAgent 选择已取消。” for `zh-CN` or "OpenAgent selection cancelled." for `en-US`. End selection; do not automatically reopen the page or continue Agent execution.
- For `status=timed_out`, terminal cleanup has already been attempted by Wait and Close Orchestration. Do not close again; explain that selection timed out and end discovery. Do not automatically reopen the page.
- This Skill handles search, wait, and browser handoff failures locally; do not silently switch Agents. Use only trusted Tool Results, authoritative states, or stable public Host error codes. Without a stable public code, treat the error as unknown and do not retry automatically. Do not infer error category, authentication state, or retryability from message text.
- Headless failures must return the original search goal, constraints, trusted public reason, and all candidates already obtained to the current caller, without overwriting or fabricating results. For direct requests, show only a natural-language reason; hide raw results and internal fields.

**Output:** A caller-facing failure result preserving full context, or a trusted user-visible termination explanation.

**Next:** End the current discovery without silently searching again, reopening the page, or executing another Agent.

## Shared OpenAgent Rules

### Shared Protocol References

- Reuse [the shared rules of openagent-run-agent](../openagent-run-agent/SKILL.md#shared-openagent-rules) for post-selection execution authorization, Invocations, Sessions, attachments, and execution result delivery. Referencing a protocol does not authorize execution; hand off only after Result Validation and Delivery passes.
- This Skill owns search, candidate delivery, and UI Handoff. Callers must not independently rewrite the browser opening, waiting, or cleanup protocol.

### Result and User Boundaries

- Trust only candidates, metadata, and authorization returned by the search Tool. Return headless results completely to the current caller without fabrication, reordering, or rewriting.
- Raw Tool Results, candidate IDs, selection handles, and Widget metadata are for internal use only. Display `handoff_url` only as the target of this flow's Browser Handoff link; do not output bare URLs, extracted tokens, or diagnostic logs.

### Browser Display Boundary

- Use only browser tools and schemas actually exposed by the current Muse host and applicable to the current task. If opening, querying, or closing is unsupported, truthfully leave that step unconfirmed. Do not install another client's runtime or guess directories, tool names, or hidden panel APIs.
- Follow Browser Handoff when opening pages. A tool reporting successful navigation proves only the state it explicitly reports; it cannot replace evidence of page visibility. Do not continuously poll page loading or repeatedly open the same URL.
- Clean up only selection tabs explicitly created in the current flow and identified by trusted handles. Preserve pre-existing tabs, tabs opened by the user whose ownership is unconfirmed, other tabs on the same domain, and Agent result pages. Do not close tabs in bulk by domain.
- After closing, if the Host supports tab queries, read back once to check whether the target disappeared and existing tabs were preserved. If a close or readback receipt is missing, record closure as unconfirmed; do not treat `selected`, `cancelled`, or `timed_out` as proof of browser closure. Keep the browser when other tabs exist; do not invent a panel-hiding capability.

### Wait and Close Orchestration

1. After handing off the original selection link, call `openagent_wait_for_selection(selection_id=<original-trusted-handle>)` directly using the actual current tool name, with only one active wait per session. Do not wrap it in another client's executor template or implement MCP yourself over HTTP.
2. While waiting is incomplete, resume the same call only through long-running calls or continuation mechanisms currently supported by Muse. Do not end the current Turn and require another user message before waiting, search again, or start parallel wait calls. If the Host cannot continue waiting, times out, or disconnects, preserve the original selection session and report its state as unconfirmed; do not fabricate selection, cancellation, or closure results.
3. For `more_requested`, retain the same session, pass the new URL back to Browser Handoff, then wait sequentially; do not perform terminal cleanup at this point. After `selected`, `cancelled`, or `timed_out` returns, preserve the original result first, then attempt terminal cleanup once for the current flow's selection tab under Browser Display Boundary.
4. The cleanup gate must contain the current flow's actual close receipt and any available readback receipt, or the specific reason each step could not be performed. If tools or trusted handles are missing, skip unsafe closing and record it as unconfirmed. Do not treat plans, Skill text, or a terminal selection state as cleanup evidence. Handle cleanup before the next stage update, execution Skill handoff, or final reply, and do not attempt it again afterward.
5. Cleanup failure must not overwrite the original selection result, expand authorization, or rerun discovery or business execution. Pass the complete original wait result to the next stage, preserving the existing contract that selection does not authorize a business task.
