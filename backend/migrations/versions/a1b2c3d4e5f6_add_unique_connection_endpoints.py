"""add unique constraint on connection endpoints

Revision ID: a1b2c3d4e5f6
Revises: 7d2f4c1a9b3e
Create Date: 2026-08-17 12:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "7d2f4c1a9b3e"
branch_labels = None
depends_on = None

# Columns that define the identity of a connection. ``connection_type``
# is intentionally excluded so the same physical link cannot be recorded
# twice under different types.
ENDPOINT_COLUMNS = [
    "source_device_id",
    "target_device_id",
    "source_port_id",
    "target_port_id",
    "source_interface_id",
    "target_interface_id",
]

CONSTRAINT_NAME = "uq_connections_device_ports"


def upgrade():
    # Safe for existing data: the current connections differ in their
    # endpoint columns, so no duplicates are present. batch_alter_table
    # is used so the constraint works on SQLite (table rebuild) and
    # PostgreSQL alike.
    with op.batch_alter_table("connections", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            CONSTRAINT_NAME,
            ENDPOINT_COLUMNS,
        )


def downgrade():
    with op.batch_alter_table("connections", schema=None) as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")