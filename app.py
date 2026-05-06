"""
AI Impact on IT Consulting Survey Interactive Dashboard
Run:  python app.py
Then open http://127.0.0.1:8050
"""

import copy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, ALL, ctx, no_update
import dash_bootstrap_components as dbc

from etl import run_etl, LIKERT_ORDER, FREQUENCY_ORDER, EXPERIENCE_ORDER
from classifications import load_classifications, save_classifications

# ── Load data ─────────────────────────────────────────────────────────────────
etl = run_etl()
wide: pd.DataFrame = etl["wide"]
questions: dict = etl["questions"]
q4_options: list = etl["q4_options"]

LIKERT_COLORS = px.colors.diverging.RdYlGn
BINARY_COLORS = {"Yes": "#4CAF50", "No": "#F44336"}

Q_LABELS = {
    1: "Current Role",
    2: "AI Usage Frequency",
    3: "Years in Consulting",
    4: "Professional Focus Areas",
    5: "AI improves daily efficiency",
    6: "AI supports technical problem-solving",
    7: "Which technical problems (open text)",
    8: "AI handles routine tasks",
    9: "Which routine tasks (open text)",
    10: "AI reduces importance of traditional skills",
    11: "Which traditional skills (open text)",
    12: "Client communication stays human",
    13: "Contextual understanding difficult for AI",
    14: "Strategic decisions should stay human",
    15: "AI tool competence becoming important",
    16: "Role shifting from execution to orchestration",
    17: "AI will significantly change consulting in 3 years",
    18: "Most important future skill (open text)",
    19: "Task least suitable for AI (open text)",
}

ROLE_OPTIONS = [{"label": r, "value": r} for r in sorted(wide["q1"].dropna().unique())]
FREQ_OPTIONS = [{"label": f, "value": f} for f in FREQUENCY_ORDER if f in wide["q2"].cat.categories]
EXP_OPTIONS  = [{"label": e, "value": e} for e in EXPERIENCE_ORDER if e in wide["q3"].cat.categories]
FOCUS_OPTIONS = [{"label": o, "value": o} for o in q4_options]

SHORT_Q = {k: f"Q{k}: {v}" for k, v in Q_LABELS.items()}

# Questions suitable for each chart type
LIKERT_QS   = [5, 12, 13, 14, 15, 16, 17]
BINARY_QS   = [6, 8, 10]
SINGLE_CAT_QS = [1, 2, 3]
MULTI_CAT_QS = [4]
OPEN_TEXT_QS  = [7, 9, 11, 18, 19]


# ── App layout ────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="AI x Consulting Survey",
)

FILTER_CARD = dbc.Card(
    [
        dbc.CardHeader(html.H5("Filters (Q1–Q4)", className="mb-0")),
        dbc.CardBody(
            [
                html.Label("Q1 – Current Role", className="fw-bold"),
                dcc.Dropdown(
                    id="filter-role",
                    options=ROLE_OPTIONS,
                    multi=True,
                    placeholder="All roles",
                    className="mb-3",
                ),
                html.Label("Q2 – AI Usage Frequency", className="fw-bold"),
                dcc.Dropdown(
                    id="filter-freq",
                    options=FREQ_OPTIONS,
                    multi=True,
                    placeholder="All frequencies",
                    className="mb-3",
                ),
                html.Label("Q3 – Years in Consulting", className="fw-bold"),
                dcc.Dropdown(
                    id="filter-exp",
                    options=EXP_OPTIONS,
                    multi=True,
                    placeholder="All experience levels",
                    className="mb-3",
                ),
                html.Label("Q4 – Professional Focus Areas", className="fw-bold"),
                dcc.Dropdown(
                    id="filter-focus",
                    options=FOCUS_OPTIONS,
                    multi=True,
                    placeholder="All focus areas",
                    className="mb-3",
                ),
                html.Div(id="respondent-count", className="text-muted small"),
            ]
        ),
    ],
    className="h-100 shadow-sm",
)

CHART_CARD = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row(
                [
                    dbc.Col(html.H5("Chart", className="mb-0"), width="auto"),
                    dbc.Col(
                        dcc.Dropdown(
                            id="q-select",
                            options=[{"label": SHORT_Q[q], "value": q} for q in range(1, 20)],
                            value=5,
                            clearable=False,
                            style={"minWidth": "420px"},
                        ),
                        width="auto",
                    ),
                    dbc.Col(
                        dcc.RadioItems(
                            id="chart-type",
                            options=[
                                {"label": " Bar", "value": "bar"},
                                {"label": " Pie", "value": "pie"},
                                {"label": " Horizontal Bar", "value": "hbar"},
                            ],
                            value="bar",
                            inline=True,
                            inputStyle={"marginRight": "4px"},
                            labelStyle={"marginRight": "12px"},
                        ),
                        width="auto",
                    ),
                ],
                align="center",
                className="g-2",
            )
        ),
        dbc.CardBody([
            html.Div(id="full-question-text", className="text-muted fst-italic small mb-2", style={"whiteSpace": "normal"}),
            dcc.Graph(id="main-chart", style={"height": "460px"}),
        ]),
    ],
    className="shadow-sm",
)

OPEN_TEXT_CARD = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row(
                [
                    dbc.Col(html.H5("Open-text Responses", className="mb-0"), width="auto"),
                    dbc.Col(
                        dcc.Dropdown(
                            id="text-q-select",
                            options=[{"label": SHORT_Q[q], "value": q} for q in OPEN_TEXT_QS],
                            value=18,
                            clearable=False,
                            style={"minWidth": "320px"},
                        ),
                        width="auto",
                    ),
                ],
                align="center",
                className="g-2",
            )
        ),
        dbc.CardBody(
            [
                html.Div(id="open-full-question-text", className="text-muted fst-italic small mb-3", style={"whiteSpace": "normal"}),
                dbc.Row(
                    [
                        # ── Left: response list ──────────────────────────────
                        dbc.Col(
                        [
                            html.P(
                                "Click a response to select it (blue), then click a class to assign it.",
                                className="text-muted small mb-2",
                            ),
                            html.Div(
                                id="text-responses",
                                style={"maxHeight": "520px", "overflowY": "auto"},
                            ),
                        ],
                        width=7,
                        ),
                        # ── Right: classification panel ───────────────────────
                        dbc.Col(
                        [
                            html.H6("Classes", className="fw-bold mb-2"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="new-class-input",
                                        placeholder="New class name…",
                                        size="sm",
                                    ),
                                    dbc.Button(
                                        "+ Add",
                                        id="add-class-btn",
                                        color="primary",
                                        size="sm",
                                        n_clicks=0,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(id="class-panel"),
                            html.Hr(),
                            dbc.Button(
                                "Save classifications",
                                id="save-classifications-btn",
                                color="success",
                                size="sm",
                                n_clicks=0,
                            ),
                            html.Small(id="save-status", className="text-success ms-2"),
                        ],
                        width=5,
                        ),
                    ]
                ),
            ]
        ),
    ],
    className="shadow-sm mt-3",
)

app.layout = dbc.Container(
    [
        dcc.Store(id="classifications-store", data=load_classifications()),
        dcc.Store(id="selected-response-store", data=None),
        dcc.Store(id="active-class-filter-store", data=None),
        dbc.Row(
            dbc.Col(
                html.H2(
                    "The Impact of AI on IT Consulting – Survey Dashboard",
                    className="text-primary my-3",
                )
            )
        ),
        dbc.Row(
            [
                dbc.Col(FILTER_CARD, width=3),
                dbc.Col(
                    [CHART_CARD, OPEN_TEXT_CARD],
                    width=9,
                ),
            ],
            className="g-3",
        ),
    ],
    fluid=True,
    className="pb-5",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def apply_filters(roles, freqs, exps, focuses):
    df = wide.copy()
    if roles:
        df = df[df["q1"].isin(roles)]
    if freqs:
        df = df[df["q2"].isin(freqs)]
    if exps:
        df = df[df["q3"].isin(exps)]
    if focuses:
        # keep respondents who have ALL selected focuses (AND logic)
        def has_focus(cell):
            if pd.isna(cell):
                return False
            parts = [p.strip() for p in str(cell).split("|")]
            return all(f in parts for f in focuses)
        df = df[df["q4"].apply(has_focus)]
    return df


def make_bar(counts: pd.Series, title: str, color_seq=None, category_orders=None):
    fig = px.bar(
        x=counts.index.tolist(),
        y=counts.values,
        labels={"x": "", "y": "Responses"},
        title=title,
        color=counts.index.tolist(),
        color_discrete_sequence=color_seq or px.colors.qualitative.Bold,
        category_orders=category_orders or {},
        text=counts.values,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="%{x}<br>Responses: %{y}<extra></extra>",
    )
    fig.update_layout(showlegend=False, margin=dict(t=50, b=40))
    return fig


def make_hbar(counts: pd.Series, title: str, color_seq=None, category_orders=None):
    fig = px.bar(
        y=counts.index.tolist(),
        x=counts.values,
        orientation="h",
        labels={"y": "", "x": "Responses"},
        title=title,
        color=counts.index.tolist(),
        color_discrete_sequence=color_seq or px.colors.qualitative.Bold,
        category_orders=category_orders or {},
        text=counts.values,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="%{y}<br>Responses: %{x}<extra></extra>",
    )
    fig.update_layout(showlegend=False, margin=dict(t=50, l=180))
    return fig


def make_pie(counts: pd.Series, title: str, color_seq=None):
    fig = px.pie(
        names=counts.index.tolist(),
        values=counts.values,
        title=title,
        color_discrete_sequence=color_seq or px.colors.qualitative.Bold,
        hole=0.3,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(t=50))
    return fig


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("main-chart", "figure"),
    Output("respondent-count", "children"),
    Output("text-responses", "children"),
    Output("full-question-text", "children"),
    Output("open-full-question-text", "children"),
    Input("filter-role", "value"),
    Input("filter-freq", "value"),
    Input("filter-exp", "value"),
    Input("filter-focus", "value"),
    Input("q-select", "value"),
    Input("chart-type", "value"),
    Input("text-q-select", "value"),
    Input("classifications-store", "data"),
    Input("selected-response-store", "data"),
    Input("active-class-filter-store", "data"),
)
def update_dashboard(roles, freqs, exps, focuses, q_num, chart_type, text_q_num, clf_store, selected_resp, active_filter):
    clf_store = clf_store or {}
    df = apply_filters(roles or [], freqs or [], exps or [], focuses or [])
    n = len(df)
    count_label = f"Showing {n} of {len(wide)} respondents"

    col = f"q{q_num}"
    q_label = Q_LABELS.get(q_num, f"Q{q_num}")
    title = f"Q{q_num}: {q_label}"

    # ── Chart ─────────────────────────────────────────────────────────────────
    if q_num in OPEN_TEXT_QS:
        fig = go.Figure()
        fig.add_annotation(
            text="Open-text question – see responses below",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#888"),
        )
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, title=title)

    elif q_num == 4:
        # Multi-select: expand pipe values
        all_vals = []
        for cell in df[col].dropna():
            all_vals.extend([p.strip() for p in str(cell).split("|") if p.strip()])
        counts = pd.Series(all_vals).value_counts().sort_values(ascending=False)
        if chart_type == "pie":
            fig = make_pie(counts, title)
        elif chart_type == "hbar":
            fig = make_hbar(counts, title)
        else:
            fig = make_bar(counts, title)

    elif q_num in LIKERT_QS:
        counts = df[col].value_counts().reindex(LIKERT_ORDER).dropna()
        if chart_type == "pie":
            fig = make_pie(counts, title, color_seq=LIKERT_COLORS)
        elif chart_type == "hbar":
            fig = make_hbar(counts, title, color_seq=LIKERT_COLORS, category_orders={"y": LIKERT_ORDER})
        else:
            fig = make_bar(counts, title, color_seq=LIKERT_COLORS, category_orders={"x": LIKERT_ORDER})

    elif q_num in BINARY_QS:
        counts = df[col].value_counts()
        colors = [BINARY_COLORS.get(k, "#999") for k in counts.index]
        if chart_type == "pie":
            fig = make_pie(counts, title, color_seq=colors)
        elif chart_type == "hbar":
            fig = make_hbar(counts, title, color_seq=colors)
        else:
            fig = make_bar(counts, title, color_seq=colors)

    elif q_num == 2:
        counts = df[col].value_counts().reindex(FREQUENCY_ORDER).dropna()
        if chart_type == "pie":
            fig = make_pie(counts, title)
        elif chart_type == "hbar":
            fig = make_hbar(counts, title, category_orders={"y": FREQUENCY_ORDER})
        else:
            fig = make_bar(counts, title, category_orders={"x": FREQUENCY_ORDER})

    elif q_num == 3:
        counts = df[col].value_counts().reindex(EXPERIENCE_ORDER).dropna()
        if chart_type == "pie":
            fig = make_pie(counts, title)
        elif chart_type == "hbar":
            fig = make_hbar(counts, title, category_orders={"y": EXPERIENCE_ORDER})
        else:
            fig = make_bar(counts, title, category_orders={"x": EXPERIENCE_ORDER})

    else:
        counts = df[col].value_counts()
        if chart_type == "pie":
            fig = make_pie(counts, title)
        elif chart_type == "hbar":
            fig = make_hbar(counts, title)
        else:
            fig = make_bar(counts, title)

    # ── Open text ─────────────────────────────────────────────────────────────
    text_col = f"q{text_q_num}"
    q_key = f"q{text_q_num}"
    q_classes = clf_store.get(q_key, {})
    selected_text = (
        selected_resp.get("text")
        if selected_resp and selected_resp.get("q") == q_key
        else None
    )
    text_items = df[["email", text_col]].dropna(subset=[text_col]).reset_index(drop=True)
    # Apply class filter if active
    if active_filter and active_filter in q_classes:
        filtered_texts = set(q_classes[active_filter])
        text_items = (
            text_items[text_items[text_col].isin(filtered_texts)].reset_index(drop=True)
        )
    text_elems = []
    for i, row in text_items.iterrows():
        display_email = str(row["email"]) if row["email"] != "anonymous" else "Anonymous"
        resp_text = str(row[text_col])
        is_selected = resp_text == selected_text
        # Class badges for this response
        badges = [
            dbc.Badge(cls, color="info", className="me-1")
            for cls, cls_resps in q_classes.items()
            if resp_text in cls_resps
        ]
        text_elems.append(
            html.Div(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Small(display_email, className="text-muted"),
                                        width="auto",
                                    ),
                                    dbc.Col(html.Div(badges), className="text-end"),
                                ],
                                className="mb-1",
                            ),
                            html.P(resp_text, className="mb-0"),
                        ]
                    ),
                    className="mb-2",
                    style={
                        "border": "2px solid #0d6efd" if is_selected else "1px solid rgba(0,0,0,.125)",
                        "backgroundColor": "#f0f7ff" if is_selected else "",
                    },
                ),
                id={"type": "response-card", "index": i},
                n_clicks=0,
                style={"cursor": "pointer"},
            )
        )
    if not text_elems:
        text_elems = [html.P("No responses for current filter.", className="text-muted")]

    return fig, count_label, text_elems, questions.get(q_num, ""), questions.get(text_q_num, "")


# ── Classification callbacks ──────────────────────────────────────────────────

@callback(
    Output("class-panel", "children"),
    Input("classifications-store", "data"),
    Input("text-q-select", "value"),
    Input("selected-response-store", "data"),
    Input("active-class-filter-store", "data"),
)
def render_class_panel(store, q_num, selected_resp, active_filter):
    store = store or {}
    q_key = f"q{q_num}"
    q_classes = store.get(q_key, {})
    if not q_classes:
        return html.P("No classes yet. Add one above.", className="text-muted small")

    has_selection = selected_resp is not None and selected_resp.get("q") == q_key
    rows = []
    for class_name, class_responses in q_classes.items():
        count = len(class_responses)
        is_active = active_filter == class_name
        is_assigned = has_selection and selected_resp["text"] in class_responses
        badge_color = "success" if is_assigned else "primary"
        if has_selection:
            action_hint = " ← remove" if is_assigned else " ← assign"
        elif is_active:
            action_hint = " ← filtering"
        else:
            action_hint = ""

        rows.append(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Span(class_name, className="fw-semibold"),
                                        dbc.Badge(count, color=badge_color, className="ms-2"),
                                        html.Small(action_hint, className="text-muted ms-1"),
                                    ],
                                    className="py-2 px-3",
                                ),
                                style={
                                    "borderColor": "#0d6efd" if is_active else "",
                                    "backgroundColor": "#e8f4f8" if is_active else "",
                                },
                            ),
                            id={"type": "class-card", "name": class_name},
                            n_clicks=0,
                            style={"cursor": "pointer"},
                        ),
                    ),
                    dbc.Col(
                        html.Button(
                            "\u2715",
                            id={"type": "delete-class-btn", "name": class_name},
                            className="btn btn-sm btn-outline-danger",
                            n_clicks=0,
                            title="Delete this class",
                        ),
                        width="auto",
                        className="ps-0 d-flex align-items-center",
                    ),
                ],
                className="mb-2 g-1",
                align="center",
            )
        )
    return rows


@callback(
    Output("selected-response-store", "data", allow_duplicate=True),
    Input({"type": "response-card", "index": ALL}, "n_clicks"),
    State({"type": "response-card", "index": ALL}, "id"),
    State("selected-response-store", "data"),
    State("text-q-select", "value"),
    State("filter-role", "value"),
    State("filter-freq", "value"),
    State("filter-exp", "value"),
    State("filter-focus", "value"),
    State("active-class-filter-store", "data"),
    State("classifications-store", "data"),
    prevent_initial_call=True,
)
def select_response(
    n_clicks_list, ids, current_selected, q_num,
    roles, freqs, exps, focuses, active_filter, clf_store
):
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict) or triggered.get("type") != "response-card":
        return no_update
    clicked_idx = triggered["index"]
    n_for_clicked = next(
        (n for n, id_ in zip(n_clicks_list, ids) if id_["index"] == clicked_idx),
        None,
    )
    if not n_for_clicked:
        return no_update

    df = apply_filters(roles or [], freqs or [], exps or [], focuses or [])
    text_col = f"q{q_num}"
    q_key = f"q{q_num}"
    q_classes = (clf_store or {}).get(q_key, {})
    text_series = df[text_col].dropna().reset_index(drop=True)
    if active_filter and active_filter in q_classes:
        filtered_texts = set(q_classes[active_filter])
        text_series = text_series[text_series.isin(filtered_texts)].reset_index(drop=True)
    if clicked_idx >= len(text_series):
        return no_update
    resp_text = str(text_series.iloc[clicked_idx])
    # Toggle: deselect if same card clicked again
    if (
        current_selected
        and current_selected.get("text") == resp_text
        and current_selected.get("q") == q_key
    ):
        return None
    return {"text": resp_text, "q": q_key}


@callback(
    Output("classifications-store", "data", allow_duplicate=True),
    Output("active-class-filter-store", "data", allow_duplicate=True),
    Output("selected-response-store", "data", allow_duplicate=True),
    Input({"type": "class-card", "name": ALL}, "n_clicks"),
    Input({"type": "delete-class-btn", "name": ALL}, "n_clicks"),
    State("selected-response-store", "data"),
    State("text-q-select", "value"),
    State("classifications-store", "data"),
    State("active-class-filter-store", "data"),
    prevent_initial_call=True,
)
def handle_class_interactions(
    card_clicks, delete_clicks, selected_resp, q_num, store, active_filter
):
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update, no_update
    # Guard against remount triggers (n_clicks reset to 0)
    triggered_value = next(
        (t["value"] for t in ctx.triggered if t.get("value")),
        None,
    )
    if not triggered_value:
        return no_update, no_update, no_update

    q_key = f"q{q_num}"
    new_store = copy.deepcopy(store) if store else {}
    if q_key not in new_store:
        new_store[q_key] = {}

    t_type = triggered.get("type")
    t_name = triggered.get("name")

    if t_type == "delete-class-btn":
        new_store.get(q_key, {}).pop(t_name, None)
        new_active = None if active_filter == t_name else active_filter
        return new_store, new_active, no_update

    if t_type == "class-card":
        has_selection = selected_resp is not None and selected_resp.get("q") == q_key
        if has_selection:
            resp_text = selected_resp["text"]
            class_resps = list(new_store[q_key].get(t_name, []))
            if resp_text in class_resps:
                class_resps.remove(resp_text)  # toggle off
            else:
                class_resps.append(resp_text)  # assign
            new_store[q_key][t_name] = class_resps
            return new_store, no_update, None  # clear selection after action
        else:
            # No response selected: toggle class filter
            new_active = None if active_filter == t_name else t_name
            return no_update, new_active, no_update

    return no_update, no_update, no_update


@callback(
    Output("classifications-store", "data", allow_duplicate=True),
    Output("new-class-input", "value"),
    Input("add-class-btn", "n_clicks"),
    State("new-class-input", "value"),
    State("text-q-select", "value"),
    State("classifications-store", "data"),
    prevent_initial_call=True,
)
def add_class(n_clicks, class_name, q_num, store):
    if not n_clicks or not class_name or not class_name.strip():
        return no_update, no_update
    class_name = class_name.strip()
    q_key = f"q{q_num}"
    new_store = copy.deepcopy(store) if store else {}
    if q_key not in new_store:
        new_store[q_key] = {}
    if class_name not in new_store[q_key]:
        new_store[q_key][class_name] = []
    return new_store, ""


@callback(
    Output("active-class-filter-store", "data", allow_duplicate=True),
    Output("selected-response-store", "data", allow_duplicate=True),
    Input("text-q-select", "value"),
    prevent_initial_call=True,
)
def reset_on_question_change(_):
    return None, None


@callback(
    Output("save-status", "children"),
    Input("save-classifications-btn", "n_clicks"),
    State("classifications-store", "data"),
    prevent_initial_call=True,
)
def save_cb(n_clicks, store):
    if not n_clicks:
        return no_update
    save_classifications(store or {})
    return "Saved \u2713"


if __name__ == "__main__":
    app.run(debug=False)
