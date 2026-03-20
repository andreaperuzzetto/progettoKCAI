"""
Email notification service.
Sends daily operational briefing via SMTP.

Configuration (in .env):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)


def _build_email_html(report: dict[str, Any], restaurant_name: str) -> str:
    tomorrow = report.get("tomorrow", {})
    covers = tomorrow.get("expected_covers", 0)
    top_products = tomorrow.get("top_products", [])
    suggestions = report.get("suggestions", [])[:3]
    review = report.get("review_summary", {})
    sentiment_pos = review.get("sentiment_positive")

    products_html = "".join(
        f"<li><strong>{p['name']}</strong>: ~{p['predicted_qty']} pezzi</li>"
        for p in top_products
    ) or "<li>Nessun dato disponibile</li>"

    suggestions_html = "".join(
        f"<li>{'🔴' if s['priority'] == 'high' else '🟡' if s['priority'] == 'medium' else '🟢'} {s['message']}</li>"
        for s in suggestions
    ) or "<li>Nessun suggerimento per oggi</li>"

    sentiment_str = f"{round(sentiment_pos)}% positivo" if sentiment_pos is not None else "n/d"

    return f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #111;">🍽 Report giornaliero — {restaurant_name}</h2>
      <h3 style="color: #333;">📊 Previsione domani</h3>
      <p>Coperti attesi: <strong>{covers}</strong></p>
      <p>Top prodotti:</p>
      <ul>{products_html}</ul>
      <h3 style="color: #333;">✅ Azioni suggerite</h3>
      <ul>{suggestions_html}</ul>
      <h3 style="color: #333;">⭐ Recensioni</h3>
      <p>Sentiment: <strong>{sentiment_str}</strong></p>
      <hr style="border: 1px solid #eee; margin: 20px 0;">
      <p style="color: #999; font-size: 12px;">Restaurant Intelligence Platform</p>
    </body></html>
    """


def send_daily_email(to_email: str, restaurant_name: str, report: dict[str, Any]) -> bool:
    """
    Send daily briefing email.
    Returns True if sent, False if SMTP not configured or error.
    """
    if not settings.smtp_host or not settings.smtp_user:
        logger.info("SMTP not configured — skipping email to %s", to_email)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📋 Report giornaliero — {restaurant_name}"
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = to_email

        html_content = _build_email_html(report, restaurant_name)
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        logger.info("Daily email sent to %s for %s", to_email, restaurant_name)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False
