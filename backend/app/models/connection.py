from datetime import datetime

from sqlalchemy import UniqueConstraint

from ..extensions import db


class Connection(db.Model):
    __tablename__ = "connections"

    __table_args__ = (
        UniqueConstraint(
            "source_device_id",
            "target_device_id",
            "source_port_id",
            "target_port_id",
            "source_interface_id",
            "target_interface_id",
            name="uq_connections_device_ports",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    source_device_id = db.Column(
        db.Integer,
        db.ForeignKey("devices.id"),
        nullable=False,
    )

    target_device_id = db.Column(
        db.Integer,
        db.ForeignKey("devices.id"),
        nullable=False,
    )

    connection_type = db.Column(
        db.String(50),
        nullable=False,
        default="network",
    )

    source_port_id = db.Column(
        db.Integer,
        db.ForeignKey("ports.id"),
        nullable=True,
    )

    target_port_id = db.Column(
        db.Integer,
        db.ForeignKey("ports.id"),
        nullable=True,
    )

    source_interface_id = db.Column(
        db.Integer,
        db.ForeignKey("interfaces.id"),
        nullable=True,
    )

    target_interface_id = db.Column(
        db.Integer,
        db.ForeignKey("interfaces.id"),
        nullable=True,
    )

    description = db.Column(db.Text)

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    source_device = db.relationship(
        "Device",
        foreign_keys=[source_device_id],
        back_populates="source_connections",
    )

    target_device = db.relationship(
        "Device",
        foreign_keys=[target_device_id],
        back_populates="target_connections",
    )

    source_port = db.relationship(
        "Port",
        foreign_keys=[source_port_id],
    )

    target_port = db.relationship(
        "Port",
        foreign_keys=[target_port_id],
    )

    source_interface = db.relationship(
        "Interface",
        foreign_keys=[source_interface_id],
    )

    target_interface = db.relationship(
        "Interface",
        foreign_keys=[target_interface_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Connection "
            f"{self.source_device_id}->{self.target_device_id}>"
        )