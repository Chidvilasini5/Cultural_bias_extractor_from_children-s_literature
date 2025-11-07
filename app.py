from flask import Flask, render_template, render_template_string, request, redirect, url_for, session
import en_core_web_sm
nlp = en_core_web_sm.load()


# We'll import the analysis code from the user's existing script on-demand,
# while preventing that script's plotting code from blocking the server.
def _load_analysis_module():
    import importlib
    import matplotlib
    # Use a non-interactive backend to avoid GUI popups
    matplotlib.use('Agg', force=True)
    # Ensure plt.show() is a no-op before the module imports pyplot
    import matplotlib.pyplot as plt  # noqa: E402
    plt.show = lambda *a, **k: None
    # Lazily import the user's analysis module (may do network I/O once)
    mod = importlib.import_module('fairy_tales_without_bias_1')
    return mod

app = Flask(__name__)
app.secret_key = "change-this-secret-in-production"


def _format_report(result: dict) -> str:
    """Build a textual report matching pretty_print_report output."""
    gbs = result.get('gender_balance_score', 0)
    rds = result.get('role_diversity_score', 0)
    sp = result.get('stereotype_penalty', 0)
    gm = result.get('gender_mentions', {}) or {}
    male = gm.get('male', 0)
    female = gm.get('female', 0)

    if female and male > female * 1.5:
        bias_line = "  → Heavily biased toward male representation.\n"
    elif male and female > male * 1.5:
        bias_line = "  → Heavily biased toward female representation.\n"
    else:
        bias_line = "  → Relatively balanced gender representation.\n"

    if rds > 7:
        role_line = "Roles are well distributed across characters."
    elif rds >= 4:
        role_line = "Characters tend to be boxed into one or two common roles."
    else:
        role_line = "Highly stereotypical and limited roles."

    if sp > 7:
        stereo_line = "Minimal use of stereotypes."
    elif sp >= 4:
        stereo_line = "Some stereotypical language is used, but not excessively."
    else:
        stereo_line = "Frequent stereotypical or biased language detected."

    report = (
        f"Scale (1–10): 1 = Low, 10 = High\n\n"
        f"👥 Gender Bias:\n"
        f"- Gender Balance Score: {gbs}\n"
        f"- Gender Mentions: Male = {male}, Female = {female}\n"
        f"{bias_line}\n"
        f"🎭 Role Diversity:\n"
        f"- Role Diversity Score: {rds}\n"
        f"  → {role_line}\n\n"
        f"🧠 Stereotype Bias:\n"
        f"- Stereotype Penalty: {sp}\n"
        f"  → {stereo_line}\n"
        + ("-" * 50)
    )
    return report

@app.route('/')
def home():
    # Show any one-time report/error and then clear it so refresh returns to a clean home
    report_text = session.pop('report_text', None)
    error = session.pop('error', None)
    return render_template('index.html', report_text=report_text, error=error)


@app.get('/health')
def health():
    """Simple health check endpoint for deployment platforms."""
    return {"status": "ok"}, 200


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'GET':
        return redirect(url_for('home'))
    url = (request.form.get('url') or '').strip()
    if not url:
        return redirect(url_for('home'))
    try:
        mod = _load_analysis_module()
        analyze_fn = getattr(mod, 'analyze_book_from_url', None)
        if not callable(analyze_fn):
            raise RuntimeError('analyze_book_from_url not found in fairy_tales_without_bias_1.py')
        result = analyze_fn(url, 'Story')
        report_text = _format_report(result)
        # Store once and redirect (POST/Redirect/GET) so refresh goes back to home
        session['report_text'] = report_text
        return redirect(url_for('home'))
    except Exception as e:
        session['error'] = str(e)
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)