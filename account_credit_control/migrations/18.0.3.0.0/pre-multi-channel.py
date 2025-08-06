# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from psycopg2 import sql

_logger = logging.getLogger(__name__)

CHANNELS = ("email", "letter", "phone")


def field_exists(cr, model, field):
    table = model.replace(".", "_")
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
        WHERE table_name = %s
          AND column_name = %s
        """,
        (table, field),
    )
    return cr.fetchone()


def _update_channel_line(cr):
    if not field_exists(cr, "credit.control.line", "channel"):
        return
    cr.execute(
        """
        ALTER TABLE credit_control_line
          ADD channel_email BOOLEAN,
          ADD channel_letter BOOLEAN,
          ADD channel_phone BOOLEAN,
          ADD email_sent BOOLEAN,
          ADD letter_sent BOOLEAN,
          ADD phone_sent BOOLEAN
        """,
    )  # pylint: disable=no-sql-injection
    count = 0
    for chan in CHANNELS:
        query = sql.SQL(
            "UPDATE credit_control_line SET {field} = True WHERE channel = %s"
        ).format(field=sql.Identifier(f"channel_{chan}"))
        cr.execute(query, [chan])
        count += cr.rowcount
        query = sql.SQL(
            "UPDATE credit_control_line"
            " SET {field} = True"
            " WHERE channel = %s AND state = 'sent'"
        ).format(field=sql.Identifier(f"{chan}_sent"))
        cr.execute(query, [chan])
    _logger.info("Updated Channels on %s Credit control lines", count)


def _update_channel_policy_level(cr):
    if not field_exists(cr, "credit.control.policy.level", "channel"):
        return
    cr.execute(
        """
        ALTER TABLE credit_control_policy_level
          ADD channel_email BOOLEAN,
          ADD channel_letter BOOLEAN,
          ADD channel_phone BOOLEAN
        """,
    )
    count = 0
    for chan in CHANNELS:
        query = sql.SQL(
            "UPDATE credit_control_policy_level SET {field} = True WHERE channel = %s"
        ).format(field=sql.Identifier(f"channel_{chan}"))
        cr.execute(query, [chan])
        count += cr.rowcount
    _logger.info("Updated Channels on %s Credit control policy levels")


def migrate(cr, version):
    _update_channel_line(cr)
    _update_channel_policy_level(cr)
