from types import SimpleNamespace

from Graph.SubGraphs.AnalystGraph.Prompts import SQLgen_prompt


def test_sqlgen_prompt_is_compact_and_contains_plan_context():
    plan = SimpleNamespace(
        title="Top categories",
        brief="Find top categories by revenue",
        related_table=["sales", "products"],
        required_columns=["sales.amount", "products.category"],
        metrics=["SUM(sales.amount)"],
        dimensions=["products.category"],
        filters=["sales.status = 'active'"],
        grain="category",
        ranking={"entity": "category", "metric": "revenue", "top_n": 10},
        depends_on=[],
        output={"category": "string", "revenue": "numeric"},
    )

    prompt = SQLgen_prompt("Show the top product categories", plan, "unused schema")

    assert "USER QUERY" in prompt
    assert "Tables:" in prompt
    assert "Required columns:" in prompt
    assert "Return JSON" in prompt
    assert len(prompt) < 4000
