"""CLI entrypoint for headless analysis."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="StockPredict — Multi-horizon US equity analysis")
console = Console()


def _print_report(report_data: dict):
    """Pretty-print a report to the console."""
    ticker = report_data.get("ticker", "?")
    price = report_data.get("as_of_price")
    change = report_data.get("price_change_pct")

    console.print(f"\n[bold]{ticker}[/bold]", end="")
    if report_data.get("company_name"):
        console.print(f" — {report_data['company_name']}", end="")
    if price:
        console.print(f"  ${price:.2f}", end="")
    if change:
        color = "green" if change > 0 else "red"
        console.print(f"  [{color}]{change:+.2%}[/{color}]")
    else:
        console.print()

    # Scores table
    table = Table(title="Horizon Scores")
    table.add_column("Horizon", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Verdict", style="bold")
    table.add_column("Confidence", justify="right")

    for key, label in [("short_term", "Short"), ("medium_term", "Medium"), ("long_term", "Long")]:
        h = report_data.get(key)
        if h:
            score = h.get("raw_score", h.get("score", "N/A"))
            verdict = h.get("verdict", "N/A")
            conf = h.get("confidence", 0)
            color = "green" if "Buy" in str(verdict) else "red" if "Sell" in str(verdict) else "yellow"
            table.add_row(label, f"{score}", f"[{color}]{verdict}[/{color}]", f"{conf:.0%}")

    console.print(table)

    # AI Summary
    if report_data.get("ai_summary"):
        console.print("\n[bold]AI Analysis[/bold]")
        console.print(report_data["ai_summary"])

    # Caveats
    caveats = report_data.get("caveats", [])
    if caveats:
        console.print("\n[dim]Caveats:[/dim]")
        for c in caveats:
            console.print(f"  [dim]• {c}[/dim]")


@app.command()
def analyze(
    tickers: list[str] = typer.Argument(help="Stock ticker(s) to analyze"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI analysis"),
    no_ml: bool = typer.Option(False, "--no-ml", help="Skip ML prediction"),
    output_dir: str = typer.Option(None, "--output-dir", "-o", help="Output directory for reports"),
):
    """Analyze one or more stock tickers."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from config.settings import get_settings
    from stockpredict.pipeline import run_analysis

    settings = get_settings()
    if no_ai:
        settings.ai.ai_enabled = False
    if no_ml:
        settings.ml.enabled = False

    out_dir = Path(output_dir) if output_dir else settings.reports_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    async def run():
        for ticker in tickers:
            console.print(f"\n[bold blue]Analyzing {ticker.upper()}...[/bold blue]")

            async def progress(update):
                console.print(f"  [{update.progress:3d}%] {update.message}")

            report = await run_analysis(
                ticker=ticker,
                settings=settings,
                progress_callback=progress,
            )

            # Print to console
            _print_report(report.model_dump())

            # Save JSON
            ts = report.generated_at.strftime("%Y%m%dT%H%M%S")
            json_path = out_dir / f"{ticker.upper()}_{ts}.json"
            json_path.write_text(report.model_dump_json(indent=2))
            console.print(f"\n  Report saved: {json_path}")

    asyncio.run(run())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the web server."""
    import uvicorn

    uvicorn.run(
        "stockpredict.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    app()
