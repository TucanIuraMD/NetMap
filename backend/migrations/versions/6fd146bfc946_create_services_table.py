"""create services table

Revision ID: 6fd146bfc946
Revises: 26ca80db290c
Create Date: 2026-08-08 15:35:43.957817
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '6fd146bfc946'
down_revision = '26ca80db290c'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    # services уже могла быть создана предыдущей неудачной попыткой
    if "services" not in inspector.get_table_names():
        op.create_table(
            "services",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # Добавляем связь ports -> services
    with op.batch_alter_table("ports", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("service_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_ports_service_id_services",
            "services",
            ["service_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("ports", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_ports_service_id_services",
            type_="foreignkey",
        )
        batch_op.drop_column("service_id")

    op.drop_table("services")