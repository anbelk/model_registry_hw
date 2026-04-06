from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registered_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("team", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_registered_models_name", "registered_models", ["name"], unique=True)
    op.create_index("ix_registered_models_team", "registered_models", ["team"], unique=False)

    json_type = postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == "postgresql" else sa.JSON()
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("registered_models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=32), server_default="none", nullable=False),
        sa.Column("parameters", json_type, nullable=False),
        sa.Column("metrics", json_type, nullable=False),
        sa.Column("tags", json_type, nullable=False),
        sa.Column("artifact_uri", sa.String(length=1024), nullable=True),
        sa.Column("run_id", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("model_id", "version", name="uq_model_version"),
    )
    op.create_index("ix_model_versions_model_id", "model_versions", ["model_id"], unique=False)
    op.create_index("ix_model_versions_stage", "model_versions", ["stage"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_model_versions_stage", table_name="model_versions")
    op.drop_index("ix_model_versions_model_id", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index("ix_registered_models_team", table_name="registered_models")
    op.drop_index("ix_registered_models_name", table_name="registered_models")
    op.drop_table("registered_models")
