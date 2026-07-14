# import json

# def SQLgen_prompt(query, plan, schema,dependencies=None):
#     return f"""
# You are an expert PostgreSQL analytics engineer.

# Generate optimized executable PostgreSQL for the analytical plan.

# USER QUERY:
# {query}

# PLAN:
# {plan}

# SCHEMA:
# {schema}
# DEPENDENCIES:
# {dependencies}

# RULES:
# - Generate SQL only for computable tasks.
# - If required columns are missing:
#   {{
#     "description": "Cannot generate SQL because ...",
#     "sql_query": null
#   }}
# -if dependencies : generate SQL only for the current subplan and use dependencies outputs as CTEs or temp tables, do not generate SQL for dependencies, they will be executed separately and their results will be passed to the current subplan.

# METRIC SAFETY:
# - Do not invent metrics.
# - Never treat negative sales as loss.
# - Compute profit/margin only if derivable.
# - Use proxy metrics only if explicitly defined in the plan.

# SCHEMA RULES:
# Use only:
# - related_table tables
# - required_columns
# - schema-defined columns

# JOINS:
# - Infer only from matching keys or obvious IDs.
# - No invented FK relationships.
# - No unnecessary joins.

# POSTGRESQL:
# - Valid standalone SQL
# - WITH clauses inside sql_query
# - End with ;
# - Explicit aliases
# - Use backticks for column/table identifiers (e.g., `column_name`)
# - No ambiguous refs
# - Correct GROUP BY
# - No invalid tables/columns

# SQL RULES:
# 1. No SELECT *
# 2. Select only required fields/metrics
# 3. Aggregate to requested grain
# 4. Respect output_control.max_rows
# 5. If allow_raw_rows=false, aggregate/rank/scalarize
# 6. LIMIT requires deterministic ORDER BY
# 7. No raw transaction rows unless allowed
# 8. Use CTEs for intermediate metrics
# 9. Final SELECT returns only analytical output

# QUARTER LOGIC:
# Use:
# DATE_TRUNC('quarter', t.`DateColumn`)

# For quarter comparisons:
# WITH date_ranges AS (
#   SELECT
#     DATE_TRUNC('quarter', CURRENT_DATE) AS current_q_start,
#     DATE_TRUNC('quarter', CURRENT_DATE) - INTERVAL '3 months' AS prev_q_start
# )

# Never use:
# EXTRACT(QUARTER FROM CURRENT_DATE) - 1

# AGGREGATION:
# - All non-aggregated columns in GROUP BY
# - Use clear aliases
# - Prefer grouping by expressions directly

# OUTPUT:
# Return only valid JSON:

# {{
#   "description": "",
#   "sql_query": ""
# }}

# ANALYTICAL OUTPUT CONTROL:

# When the requested grain can produce a very large result set
# (e.g. city_product, customer_product, city_customer_product,
# product_date, customer_date):

# 1. Prefer analytical summarization over exhaustive enumeration.

# 2. If the plan contains concepts such as:
#    - highest
#    - top
#    - best
#    - leading
#    - most popular
#    - most revenue
#    - highest sales
#    - top-performing
#    - largest contributors

#    then generate ranking logic using:
#    ROW_NUMBER(),
#    RANK(),
#    or DENSE_RANK().

# 3. For hierarchical analysis:
#    Example:
#    "highest revenue cities and their most popular products"

#    First identify top cities,
#    then rank products within each city,
#    instead of returning every city-product combination.

# 4. Respect analytical usefulness:
#    Do not return thousands of rows when a ranked summary
#    answers the question more effectively.

# 5. If output_control.max_rows is absent:
#    - Prefer Top 10 groups at the primary grain.
#    - Prefer Top 5 members within each group.
#    - Keep result size generally below 200 rows.

# 6. For grouped rankings:
#    Use:

#    ROW_NUMBER() OVER (
#        PARTITION BY <group>
#        ORDER BY <metric> DESC
#    )

#    and filter on rank.

# 7. When title or query contains:
#    - popularity
#    - top
#    - best
#    - highest
#    - leading

#    ranking is preferred over full-detail listing.

# 8. Never return all combinations of a grain if a ranking-based
#    analytical answer better satisfies the request.

# RANKING DETERMINISM:

# If the plan contains ranking information:

# {{
#   "entity":"city",
#   "metric":"revenue",
#   "top_n":10
# }}

# SQL MUST use that exact ranking.

# Do not infer alternative top_n values.

# Do not invent additional rankings.

# Do not expand beyond the specified ranked entities.

# VALIDATE:
# 1. Tables exist
# 2. Columns exist
# 3. Joins are inferable
# 4. SQL is standalone
# 5. JSON is valid
# 6. Return JSON only
# """

# def build_sql_fix_prompt(plan, error, previous_sql, schema):
#     plan_str = json.dumps(plan, indent=2) if isinstance(plan, dict) else str(plan)

#     return f"""
# You are an expert SQL engineer.

# Fix the failed SQL using the plan and error.

# PLAN:
# {plan_str}

# SCHEMA:
# {schema}

# FAILED SQL:
# {previous_sql}

# ERROR:
# {error}

# RULES:
# 1. Preserve business logic unless required.
# 2. Make minimal fixes.
# 3. Return only corrected SQL.
# 4. Return a valid json 

# SCHEMA:
# - Use only valid tables/columns.
# - Use only related_table tables.
# - No invented joins.

# POSTGRESQL:
# - Valid standalone SQL
# - WITH inside query
# - End with ;
# - Explicit aliases
# - Double-quoted columns
# - Correct GROUP BY
# - No invalid refs

# SQL RULES:
# - No SELECT *
# - Aggregate to requested grain
# - Respect output_control.max_rows
# - LIMIT requires ORDER BY
# - No raw rows unless allowed
# - Use CTEs when useful

# QUARTER RULES:
# Use:
# DATE_TRUNC('quarter', t."DateColumn")

# Never:
# EXTRACT(QUARTER FROM CURRENT_DATE) - 1

# OUTPUT:
# {{
#   "description": "",
#   "sql_query": ""
# }}

# For impossible queries:
# {{
#   "description": "Cannot generate SQL because ...",
#   "sql_query": null
# }}
# """.strip()

# def not_feasible_prompt(reason,possible_analysis,missing_requirements,alternative_queries):
#   prp=f'''You are a helpful assistant.

#   Your task is to explain to the user why their request cannot be fully fulfilled based on the provided analysis.

#   Input:
#   - reason: The primary reason the request cannot be completed.
#   - possible_analysis: Things that can still be analyzed or inferred from the available information.
#   - missing_requirements: Information, constraints, or context required to fulfill the request.
#   - alternative_queries: Similar or related queries that can be answered with the currently available information.

#   Instructions:
#   1. Clearly explain why the request cannot be fulfilled.
#   2. Use the provided reason as the main explanation.
#   3. Explain the missing requirements in a user-friendly way.
#   4. If possible, mention what analysis can still be performed.
#   5. Suggest alternative queries the user may ask instead.
#   6. Be constructive and helpful.
#   7. Do not invent new missing requirements, analyses, or alternatives.
#   8. Do not blame the user.
#   9. Do not output JSON.
#   10. Write naturally in markdown.

#   Inputs:

#   Reason:
#   {reason}

#   Possible Analysis:
#   {possible_analysis}

#   Missing Requirements:
#   {missing_requirements}

#   Alternative Queries:
#   {alternative_queries}

#   Generate a response that:
#   - Starts by explaining why the request cannot currently be fulfilled.
#   - Lists the missing information or requirements.
#   - Mentions any useful analysis that can still be done.
#   - Ends with alternative queries the user could ask.

#   '''
#   return prp

# def feasibility_prompt(query,schema,related_tables):
#   ANALYSIS_FEASIBILITY_PROMPT = f"""
#     You are a Data Analysis Feasibility Agent.

#     Determine whether the user's requested analysis can be performed using ONLY the provided database schema.

#     ### Inputs

#     User Query:
#     {query}

#     Database Schema:
#     {schema}

#     Relevant Tables:
#     {related_tables}

#     ### Decision Criteria

#     The query is **POSSIBLE** only if:

#     - All required tables exist.
#     - All required columns (metrics, dimensions, timestamps, etc.) exist.
#     - Required business terms can be mapped to available data.
#     - Required table joins are possible.

#     Otherwise return **NOT_POSSIBLE**.

#     Interpret business language only when it maps directly to measurable data.

#     Examples:
#     - "Popular products" → sales count by product (possible if sales data exists).
#     - "Top cities" → revenue grouped by city (possible if city and revenue exist).
#     - "Reasons for customer churn" → NOT_POSSIBLE unless churn reason data exists.

#     ### Evaluation Steps

#     1. Identify required tables.
#     2. Identify required columns (metrics, dimensions, time).
#     3. Verify they exist in the schema.
#     4. Verify join paths.
#     5. Decide:
#       - POSSIBLE
#       - NOT_POSSIBLE

#     ### Rules

#     - Use ONLY the provided schema.
#     - Never hallucinate tables or columns.
#     - Do NOT generate SQL.
#     - Be strict.
#     - If anything essential is missing, return NOT_POSSIBLE.
#     - When NOT_POSSIBLE:
#       - explain what is missing,
#       - suggest analyses that are possible using the current schema and are as close as possible to the user's intent.

#     ### Output

#     Return ONLY valid JSON.

#     {{
#         "status": "POSSIBLE | NOT_POSSIBLE",
#         "reason": "...",
#         "possible_analysis": [],
#         "missing_requirements": [],
#         "alternative_queries": []
#     }} """
#   return ANALYSIS_FEASIBILITY_PROMPT

# def get_output_prompt(plan_of_query):
#     prompt = f"""
# You are an AI assistant responsible for generating the FINAL USER RESPONSE.

# RULES:
# 1. Validate consistency across all outputs before generating the answer.
# 2. If any output states that data is unavailable, missing, invalid, or analysis cannot be performed:
#    - treat contradictory analytical outputs as unreliable
#    - DO NOT include conclusions derived from unavailable data
# 3. Prefer metadata/error statements over generated numerical analysis when conflicts occur.
# 4. Ignore hallucinated, contradictory, or unsupported results.
# 5. Return only information that is logically consistent.
# 6. Do NOT mention internal planning or conflict resolution.
# 7. Return ONLY the final user-facing answer.

# DATA:
# {json.dumps(plan_of_query, indent=2)}
# """
#     return prompt

# def PlannerPrompt(schema, related_tables, query):
#     return f"""
# You are an expert analytical planning agent.

# Do NOT answer the query directly.
# Create the minimum analytical plan required to answer it using the database.

# INPUTS:
# 1. Schema
# 2. Related tables
# 3. User query

# RULES:
# - Think like a senior data analyst.
# - Create only tasks that directly help answer the query.
# - Do not invent metrics.
# - Verify required columns exist before planning metrics like profit, loss, margin, churn, refund, or cost.
# - If required data is missing, create a task reporting the data gap in assumptions.
# - Never infer loss from negative sales unless explicitly defined.

# PLANNING:
# 1. No one-task-per-table plans.
# 2. No unnecessary summaries, visualizations, recommendations, duplicates, or derivable tasks.
# 3. Prefer analytical outputs over raw extraction.
# 4. Use only required tables/columns.
# 5. Required columns include:
#    - metrics
#    - dimensions
#    - date/time
#    - filters
#    - join keys
# 6. Avoid vague tasks.
# 7. Describe analytical intent, not SQL steps.
# 8. Minimize tasks while maximizing reusable outputs.
# When a query contains:

# - top
# - highest
# - best
# - leading
# - popular
# - most

# the planner MUST explicitly specify:

# 1. ranking entity
# 2. ranking metric
# 3. top_n
# 4. partition scope

# Never leave ranking implicit.

# Bad:

# {{
#   "grain":"city_product"
# }}

# Good:

# {{
#   "ranking":{{
#       "entity":"city",
#       "metric":"revenue",
#       "top_n":10
#   }}
# }}
# USE ONLY WHEN NEEDED:
# - trend analysis
# - time comparison
# - contribution analysis
# - segmentation
# - anomaly detection
# - distribution analysis
# - correlation analysis
# - drill-down

# DEPENDENCIES:
# Use depends_on only if a task requires another task's output.

# LOSS/PROFIT SAFETY:
# - Use actual profit/loss/cost columns only.
# - If unavailable, analyze revenue decline or report missing data.
# - Mention limitations in assumptions.

# ROW CONTROL:
# Each subPlan must define:
# - grain
# - output_control.max_rows
# - output_control.allow_raw_rows

# Defaults:
# - KPI: 1
# - monthly trend: 36
# - quarterly trend: 20
# - contribution: 50
# - ranking: 10–20
# - anomalies: 50
# - drill-down: 100
# - raw sample: 100

# Do not return raw transactional rows unless explicitly requested.
# Prefer aggregated outputs.
# Use top/bottom N where dimensions are large.

# OUTPUT:
# Return STRICT valid JSON only:

# {{
#   "goal": "Analyze quarterly sales trends",
#   "subPlans": {{
#     "1": {{
#       "title": "Revenue trend analysis",
#       "brief": "Analyze revenue by quarter",
#       "related_table": ["sales"],
#       "required_columns": ["revenue", "quarter"],
#       "metrics": ["revenue"],
#       "dimensions": ["quarter"],
#       "filters": [],
#       "grain": "quarter",
#       "ranking":{{
#       "entity":"city",
#       "metric":"revenue",
#       "top_n":10
#   }}
#       "depends_on": [],
#       "output": {{
#         "quarter": "string",
#         "revenue": "float"
#       }},
#       "assumptions": [],
#       "output_control": {{
#         "max_rows": 20,
#         "allow_raw_rows": false
#       }}
#     }}
#   }}
# }}

# VALIDATION:
# 1. Return only JSON.
# 2. Use subPlans, not tasks.
# 3. Tables/columns must exist in schema.
# 4. No extra keys.
# 5. No markdown.
# 6. No unnecessary tasks.

# SCHEMA:
# {schema}

# RELATED TABLES:
# {related_tables}

# USER QUERY:
# {query}
# """

import json


def SQLgen_prompt(query, plan, schema, dependencies=None):
    return f"""
Role: expert PostgreSQL analytics engineer. Task: generate optimized executable SQL for the CURRENT analytical plan only.

INPUTS
User query: {query}
Plan: {plan}
Schema: {schema}
Dependencies: {dependencies}

RULES
1. Generate SQL only for computable tasks. If required data/columns are missing return {{"description":"Cannot generate SQL because ...","sql_query":null}}.
2. If dependencies exist, do not regenerate them; use their passed outputs as CTEs/temp tables for the current subplan.
3. Use only related_table tables, required_columns, and schema-defined columns.
4. Do not invent metrics, proxy metrics, tables, columns, joins, or FK relationships; join only on matching keys/obvious IDs and avoid unnecessary joins.
5. Never treat negative sales as loss; compute profit/margin only if derivable.
6. SQL must be standalone PostgreSQL in sql_query, end with ;, use WITH when useful, explicit aliases, PostgreSQL double-quoted identifiers, no ambiguous/invalid refs, no SELECT *.
7. Select only required fields/metrics; aggregate to requested grain; GROUP BY all non-aggregated expressions; final SELECT returns only analytical output.
8. Respect output_control.max_rows. If allow_raw_rows=false, aggregate/rank/scalarize. LIMIT requires deterministic ORDER BY. No raw transaction rows unless allowed.
9. Quarter logic: use DATE_TRUNC('quarter', t."DateColumn"). For current vs previous quarter use date_ranges CTE with current_q_start=DATE_TRUNC('quarter', CURRENT_DATE), prev_q_start=current_q_start - INTERVAL '3 months'. Never use EXTRACT(QUARTER FROM CURRENT_DATE) - 1.
10. Large grains (city_product, customer_product, city_customer_product, product_date, customer_date): prefer ranked analytical summaries over exhaustive rows.
11. If plan/title/query implies highest/top/best/leading/most/popular/most revenue/highest sales/top-performing/largest contributors, use ROW_NUMBER/RANK/DENSE_RANK.
12. For hierarchy, rank parent groups first, then rank members within each parent; do not return all combinations.
13. If max_rows absent, prefer Top 10 primary groups and Top 5 members per group; generally keep output under 200 rows.
14. Grouped ranking pattern: ROW_NUMBER() OVER (PARTITION BY <group> ORDER BY <metric> DESC), then filter rank.
15. If plan has ranking like {{"entity":"city","metric":"revenue","top_n":10}}, use it exactly; do not alter top_n, add rankings, or expand entities.
16. Validate tables, columns, joins, standalone SQL, and JSON before returning.

OUTPUT ONLY valid JSON:
{{"description":"","sql_query":""}}
""".strip()


def build_sql_fix_prompt(plan, error, previous_sql, schema):
    plan_str = json.dumps(plan, indent=2) if isinstance(plan, dict) else str(plan)
    return f"""
Role: expert SQL engineer. Task: minimally fix the failed PostgreSQL using the plan, schema, previous SQL, and error.

PLAN: {plan_str}
SCHEMA: {schema}
FAILED SQL: {previous_sql}
ERROR: {error}

RULES
- Preserve business logic unless the error requires change.
- Use only valid schema/related_table tables and columns; no invented joins.
- Return standalone PostgreSQL inside valid JSON; sql_query ends with ;.
- Use WITH when useful, explicit aliases, double-quoted identifiers, correct GROUP BY, no invalid refs, no SELECT *.
- Aggregate to requested grain; respect output_control.max_rows; LIMIT requires ORDER BY; no raw rows unless allowed.
- Quarter logic: DATE_TRUNC('quarter', t."DateColumn"); never EXTRACT(QUARTER FROM CURRENT_DATE) - 1.

OUTPUT ONLY:
{{"description":"","sql_query":""}}
Impossible:
{{"description":"Cannot generate SQL because ...","sql_query":null}}
""".strip()


def not_feasible_prompt(reason, possible_analysis, missing_requirements, alternative_queries):
    return f"""
Role: helpful assistant. Explain in natural markdown why the request cannot currently be fully fulfilled.

Inputs:
Reason: {reason}
Possible analysis: {possible_analysis}
Missing requirements: {missing_requirements}
Alternative queries: {alternative_queries}

Rules: start with the main reason; list missing information in user-friendly language; mention possible analysis; end with alternative queries; be constructive; do not blame the user; do not invent anything; do not output JSON.
""".strip()


def feasibility_prompt(query, schema, related_tables):
    return f"""
Role: Data Analysis Feasibility Agent. Decide if the user analysis is POSSIBLE using ONLY the provided schema.

INPUTS
User Query: {query}
Database Schema: {schema}
Relevant Tables: {related_tables}

Decision: POSSIBLE only if all required tables, columns, metrics, dimensions, timestamps, filters, business-term mappings, and joins exist; otherwise NOT_POSSIBLE.

RULES
- Use only the provided schema; never hallucinate tables/columns; do not generate SQL; be strict.
- Interpret business terms only when directly measurable: popular products=sales count by product if sales data exists; top cities=revenue by city if city+revenue exist; churn reasons=NOT_POSSIBLE unless churn reason data exists.
- For NOT_POSSIBLE, explain missing items and suggest close analyses possible with current schema.
- Check required tables, columns, metrics/dimensions/time/filters, and join paths before deciding.

OUTPUT ONLY valid JSON:
{{"status":"POSSIBLE | NOT_POSSIBLE","reason":"...","possible_analysis":[],"missing_requirements":[],"alternative_queries":[]}}
""".strip()


def get_output_prompt(plan_of_query):
    return f"""
Role: final user-response generator. Return ONLY the final user-facing answer.

Rules: validate consistency across outputs; if any output says data is unavailable/missing/invalid/impossible, treat contradictory analysis as unreliable; prefer metadata/errors over conflicting numbers; ignore hallucinated, contradictory, or unsupported results; include only logically consistent information; do not mention internal planning/conflict resolution.

DATA:
{json.dumps(plan_of_query, indent=2)}
""".strip()


def PlannerPrompt(schema, related_tables, query):
    return f"""
Role: expert analytical planning agent. Do NOT answer the query. Create the minimum database analysis plan needed.

INPUTS
Schema: {schema}
Related tables: {related_tables}
User query: {query}

RULES
1. Think like a senior data analyst; create only tasks directly needed to answer the query.
2. Use only existing schema tables/columns and required metrics, dimensions, date/time, filters, and join keys.
3. Do not invent metrics; verify columns before planning profit/loss/margin/churn/refund/cost; if missing, create a data-gap task in assumptions.
4. Never infer loss from negative sales unless explicitly defined.
5. Avoid one-task-per-table plans, unnecessary summaries, visualizations, recommendations, duplicates, derivable tasks, vague tasks, and raw extraction unless requested.
6. Describe analytical intent, not SQL steps; minimize tasks while maximizing reusable outputs.
7. Use depends_on only when a task requires another task output.
8. Use only when needed: trend analysis, time comparison, contribution analysis, segmentation, anomaly detection, distribution analysis, correlation analysis, drill-down.
9. Loss/profit: use actual profit/loss/cost columns only; otherwise analyze revenue decline or report missing data and mention limitations in assumptions.
10. Each subPlan must define grain and output_control.max_rows/allow_raw_rows. Defaults: KPI=1, monthly trend=36, quarterly trend=20, contribution=50, ranking=10-20, anomalies=50, drill-down=100, raw sample=100. Prefer aggregates and top/bottom N for large dimensions.
11. If query contains top/highest/best/leading/popular/most, each relevant subPlan must specify ranking.entity, ranking.metric, ranking.top_n, ranking.partition_scope. Never leave ranking implicit. Bad: {{"grain":"city_product"}}. Good: {{"ranking":{{"entity":"city","metric":"revenue","top_n":10,"partition_scope":"overall"}}}}.

OUTPUT ONLY strict valid JSON, no markdown, no extra keys, use subPlans not tasks:
{{
  "goal":"Analyze quarterly sales trends",
  "subPlans":{{
    "1":{{
      "title":"Revenue trend analysis",
      "brief":"Analyze revenue by quarter",
      "related_table":["sales"],
      "required_columns":["revenue","quarter"],
      "metrics":["revenue"],
      "dimensions":["quarter"],
      "filters":[],
      "grain":"quarter",
      "ranking":{{"entity":"city","metric":"revenue","top_n":10,"partition_scope":"overall"}},
      "depends_on":[],
      "output":{{"quarter":"string","revenue":"float"}},
      "assumptions":[],
      "output_control":{{"max_rows":20,"allow_raw_rows":false}}
    }}
  }}
}}

VALIDATION: return JSON only; tables/columns must exist; no unnecessary tasks.
""".strip()
