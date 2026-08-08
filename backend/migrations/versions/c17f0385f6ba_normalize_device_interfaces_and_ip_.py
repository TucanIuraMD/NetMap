"""normalize device interfaces and ip addresses

Revision ID: c17f0385f6ba
Revises: c8c703d43f2f
Create Date: 2026-08-08 15:04:41.190427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c17f0385f6ba'
down_revision = 'c8c703d43f2f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "interfaces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("mac_address", sa.String(length=17), nullable=True),
        sa.Column("speed", sa.Integer(), nullable=True),
        sa.Column("mtu", sa.Integer(), nullable=True),
        sa.Column("interface_type", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("devices") as batch_op:
        batch_op.drop_column("ip_address")
        batch_op.drop_column("mac_address")

    with op.batch_alter_table("ip_addresses") as batch_op:
        batch_op.add_column(
            sa.Column("interface_id", sa.Integer(), nullable=True)
        )
        batch_op.drop_column("device_id")

    with op.batch_alter_table("ip_addresses") as batch_op:
        batch_op.alter_column(
            "interface_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_ip_addresses_interface_id",
            "interfaces",
            ["interface_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("ip_addresses") as batch_op:
        batch_op.drop_constraint(
            "fk_ip_addresses_interface_id",
            type_="foreignkey",
        )
        batch_op.drop_column("interface_id")
        batch_op.add_column(
            sa.Column("device_id", sa.Integer(), nullable=True)
        )

    with op.batch_alter_table("ip_addresses") as batch_op:
        batch_op.alter_column(
            "device_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_ip_addresses_device_id",
            "devices",
            ["device_id"],
            ["id"],
        )

    with op.batch_alter_table("devices") as batch_op:
        batch_op.add_column(
            sa.Column("ip_address", sa.String(length=45), nullable=True)
        )
        batch_op.add_column(
            sa.Column("mac_address", sa.String(length=17), nullable=True)
        )

    op.drop_table("interfaces")
