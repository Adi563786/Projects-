
def get_page_purpose_prompt(
    task,
    url,
    title,
    elements,
    previous_page_tasks=None,
):
    previous_page_tasks = previous_page_tasks or []

    return f"""
You determine the NEXT LOGICAL STEP on the current page.

MAIN TASK:
{task}

PREVIOUS COMPLETED PAGE TASKS:
{previous_page_tasks}

CURRENT PAGE:
URL: {url}
Title: {title}

VISIBLE ELEMENTS:
{elements}

Rules:

1. Prefer information already visible on the page.
   If visible content contains the answer needed by MAIN TASK, instruct
   reading/extracting it instead of navigating elsewhere.

2. Never repeat a completed previous task.

3. Describe the COMPLETE logical step, not an isolated UI action.

4. For search:
   - if a search query still needs to be performed and a search input exists,
     say:
     Enter "<exact query>" in the search box and submit the search.
   - NEVER say only:
     "Click the search button."
   - Clicking Search without entering the query is not a valid search task.

5. If search results already exist, do not search again.
   Instruct opening the first relevant organic result.

6. If the destination page is already open, do not click links that merely
   reopen the same page.

7. Use only controls/content actually present in VISIBLE ELEMENTS.

8. Preserve query/entity spelling from MAIN TASK when text must be entered.

Return valid json with response in  ONE short instruction sentence only.
{{
  'pageTask':'response'
}}
""".strip()




def get_action_prompts(
    original_task,
    task,
    url,
    title,
    elements,
    mutation_prompt="",
    scroll_y=0,
    viewport_height=None,
    document_height=None,
):
    is_continuation = bool(mutation_prompt.strip())

    execution_state = (
        "CONTINUATION: use mutation context to determine what remains unfinished."
        if is_continuation
        else
        "FIRST PASS: no browser actions completed yet."
    )

    mutation_context = mutation_prompt.strip() or "None"

    can_scroll_down = (
        document_height is None
        or viewport_height is None
        or scroll_y + viewport_height < document_height
    )

    return f"""
You are an autonomous browser agent using:

OBSERVE -> DECIDE -> ACT -> OBSERVE

Return ONLY the next action/observation needed to progress.
Use only this prompt and attached screenshots.
Never invent or reuse old element indices.

USER TASK:
{original_task}

PAGE TASK:
{task}

STATE:
{execution_state}

MUTATION CONTEXT:
{mutation_context}

CURRENT PAGE:
URL: {url}
Title: {title}
Scroll: {scroll_y}
Viewport: {viewport_height}
Document height: {document_height}
Can scroll down: {can_scroll_down}

CURRENT ELEMENTS:
{elements}

AVAILABLE ACTIONS:
- click
- type
- get_text
- press_key: Enter | Tab | Escape | ArrowDown | ArrowUp

TOOLS:
- get_screenshot
- scroll_mouse

====================
DECISION RULES
====================

1. Determine the NEXT UNFINISHED STEP.
2. Determine what the CURRENT PAGE already represents.
3. Find a CURRENT element that directly advances that step.
4. If a clear valid element exists, ACT on it immediately.
5. Never repeat a completed step just because its controls remain visible.
6. Screenshot only if current elements are insufficient/ambiguous.
7. Scroll only if the target is absent, may be outside the viewport, and
   scrolling is possible.
8. If complete, return {{"actions":[]}}.

CURRENT PAGE STATE overrides generic workflow.

Example:
If search results already exist, do NOT search again.
If the destination page is already open, continue extracting information.
PAGE TASK is planning guidance, not an unconditional command.

Before following PAGE TASK, validate it against:
1. MAIN USER TASK
2. CURRENT PAGE
3. CURRENT ELEMENTS

If PAGE TASK describes only part of a required operation, complete the
logical operation correctly.

Example:
If PAGE TASK says to search and the query has not been entered yet,
typing the query must happen before submission.

Never click a Search/Submit button on an empty or incorrect search field
when the task requires entering a query first.
====================
ELEMENT GROUNDING
====================

Every indexed action MUST use an index literally present in CURRENT ELEMENTS.

Never use indices from:
- previous pages
- previous observations
- screenshots
- examples
- memory

Action must be supported by element metadata:
- type -> actions contains "type"
- click -> actions contains "click"
- get_text -> readable/relevant text element

Match targets using:
text, href, role, tag, aria, placeholder, name, title, value, className,
page title, URL, order, and context.

Minor spelling/capitalization differences are acceptable when the intended
target is clear from combined evidence.

====================
SEARCH RULES
====================

Before typing into a search field, check whether relevant results ALREADY
exist.

IF relevant results exist:
- DO NOT search again.
- choose the first organic, existing, relevant result.
- prefer a real destination/content link over:
  search/query links, suggestions, navigation, create/edit links,
  missing/dead links, ads, pagination, or unrelated links.
- click its CURRENT index.
- STOP and re-observe after navigation.

IF relevant results do NOT exist:
- find the current editable search field.
- type the query and submit it IN THE SAME response:
  type -> Search button, OR type -> Enter.
- STOP after submission and re-observe.

A type action on a search field without submission in the same action list
is INVALID.

"First result" means the first valid organic relevant destination, not
necessarily the first similarly named link.

Do not search again merely to fix a minor spelling variation when a clear
matching result already exists.
SEARCH INVARIANT:

When a new search is required:

1. Find the editable search input.
2. Check its current value.
3. If it does not already contain the required query:
   type the required query.
4. Submit using Search button or Enter.

If typing and submission can be safely performed without re-observation,
return both in the same actions list.

Never submit a search before ensuring the required query is present.
====================
ACTION SEQUENCING
====================

Return the smallest useful executable sequence.

Batch only actions guaranteed valid before any page mutation.

Safe:
- click input -> type
- type search -> Enter
- type search -> click known Search button
- dropdown -> ArrowDown -> Enter

Do NOT batch across navigation/page updates.

After clicking a result, submitting a form/search, or another likely page
mutation: STOP and re-observe.

Never click a link whose href equals the current URL unless explicitly needed.

====================
CONTENT EXTRACTION
====================

When the destination page is open:
- locate only information needed for USER TASK;
- prefer the smallest/directly relevant readable element;
- use get_text;
- screenshot/scroll only if required content is unavailable.

====================
OBSERVATION / BLOCKED
====================

Request screenshot when structured elements cannot resolve the target.

Request scroll only when:
- target is absent;
- it may exist outside viewport;
- scrolling is possible.

Do not screenshot/scroll when a clear actionable target already exists.

Return BLOCKED only when the target cannot be resolved or found.

====================
OUTPUT
====================

Return exactly ONE JSON object. No Markdown or explanation.

PAGE ACTION:
{{
  "actions": [
    {{
      "action": "click | type | get_text | press_key",
      "index": "<CURRENT index; omit for press_key>",
      "text": "<type only>",
      "key": "<press_key only>"
    }}
  ]
}}

SCREENSHOT:
{{
  "tool_calls": [
    {{"name":"get_screenshot","args":{{}}}}
  ]
}}

SCROLL:
{{
  "tool_calls": [
    {{"name":"scroll_mouse","args":{{"pixels":600}}}}
  ]
}}

BLOCKED:
{{
  "blocked": {{
    "reason": "visible_element_missing_from_current_elements | ambiguous_element_match | required_content_not_found",
    "element": "<description>"
  }}
}}

COMPLETE:
{{"actions":[]}}

====================
FINAL CHECK
====================

Before returning:
- index exists in CURRENT ELEMENTS;
- action is supported;
- target matches unfinished task;
- action advances the task;
- completed steps are not repeated;
- search is not restarted if results already exist;
- search typing includes submission;
- navigation-dependent actions are not batched.

Most important rule:

IF THE NEXT TARGET ALREADY EXISTS IN CURRENT ELEMENTS, USE IT.
DO NOT RESTART THE WORKFLOW.
""".strip()


def get_task_completion_prompt(original_task, completed_summary):
    return f"""
You are an autonomous browser agent's completion-checking module.

Your ONLY job is to decide whether the ORIGINAL USER QUERY has been fully
satisfied by the work already done, based strictly on the evidence given
below. Do not assume anything was done that isn't stated.

========================
ORIGINAL USER QUERY
========================

{original_task}

========================
COMPLETED WORK SO FAR
========================

Each entry below describes one page that was visited: its title, the
specific task attempted on that page, and the outcome of that attempt.

{completed_summary}

========================
HOW TO DECIDE
========================

1. Break the ORIGINAL USER QUERY into what it actually requires — a query
   can ask for more than one thing (e.g. "find X and tell me Y about it"
   requires both finding X and extracting Y, not just one of them).

2. Check the COMPLETED WORK against every part of the query. Every required
   part must be satisfied by a page whose status indicates success — not
   merely attempted, not in progress, not partially done.

3. If any required part of the query has no corresponding successful
   completed entry, the query is NOT fulfilled, even if other parts were
   completed successfully.

4. If a page's status shows an error, a timeout, "element not found," or any
   other failure, do not count that step as fulfilling the query, even if
   it was the right page or the right attempt.

5. Do not fulfill the query based on intention or partial progress (e.g.
   "typed the search query" is not the same as "found and returned the
   requested information").

6. If COMPLETED WORK is empty or does not mention anything relevant to the
   ORIGINAL USER QUERY, the query is NOT fulfilled.

7. Do not guess or assume success beyond what the completed work explicitly
   states.

========================
OUTPUT CONTRACT
========================

Return ONLY one valid JSON object. No Markdown, no explanation, no
reasoning shown, nothing before or after it.

{{"completed": true}}

or

{{"completed": false}}

Return only the JSON object.
""".strip()   



def get_mutation_prompt(task, incompleted, completed, actions, elements):

    indexed_types = {"click", "type", "get_text"}
    needs_elements = any(
        a.get("action") in indexed_types
        for a in incompleted
    )

    current_elements = elements if needs_elements else "NOT REQUIRED"

    return f"""
You are continuing unfinished browser actions after the DOM changed.

TASK:
{task}

COMPLETED:
{completed}

REMAINING ACTIONS:
{incompleted}

CURRENT ELEMENTS:
{current_elements}

CRITICAL RULE:
REMAINING ACTIONS are authoritative.
Execute the SAME action types in the SAME order.
Do not create a different action.

Rules:

- Never repeat COMPLETED actions.
- Preserve all non-index arguments such as "text" and "key".

For click/type/get_text:
- old indices are stale;
- find the equivalent target in CURRENT ELEMENTS;
- replace ONLY the index with its current index.

For press_key:
- copy the action unchanged;
- press_key NEVER has an index;
- do NOT inspect CURRENT ELEMENTS for a replacement;
- do NOT convert press_key into click, type, or get_text.

Return multiple remaining actions if safe.
Stop after an action that may submit, navigate, reload, or invalidate the DOM.

OUTPUT ONLY JSON:

{{"actions":[...]}}

Valid forms:

{{"action":"click","index":"<current index>"}}
{{"action":"type","index":"<current index>","text":"<text>"}}
{{"action":"get_text","index":"<current index>"}}
{{"action":"press_key","key":"<key>"}}

If REMAINING ACTIONS is:
[{{"action":"press_key","key":"Enter"}}]

the output MUST be:
{{"actions":[{{"action":"press_key","key":"Enter"}}]}}

Return only JSON.
""".strip()
