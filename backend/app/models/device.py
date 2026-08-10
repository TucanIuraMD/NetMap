from datetime import datetime

from ..extensions import db


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)

    network_id = db.Column(
        db.Integer,
        db.ForeignKey("networks.id"),
        nullable=False,
    )

    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100))
    hostname = db.Column(db.String(255))
    device_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

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

    network = db.relationship(
        "Network",
        back_populates="devices",
    )

    interfaces = db.relationship(
        "Interface",
        back_populates="device",
        cascade="all, delete-orphan",
    )
    ports = db.relationship(
        "Port",
        back_populates="device",
        cascade="all, delete-orphan",
    )

    source_connections = db.relationship(
        "Connection",
        foreign_keys="Connection.source_device_id",
        back_populates="source_device",
        cascade="all, delete-orphan",
    )

    target_connections = db.relationship(
        "Connection",
        foreign_keys="Connection.target_device_id",
        back_populates="target_device",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Device {self.name}>"