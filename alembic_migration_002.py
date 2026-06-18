"""Add provider, model, generation_time columns to projects table.

Revision ID: 002_add_project_metadata
Revises: 001_initial
Create Date: 2026-06-17 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_add_project_metadata"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to projects table."""
    op.add_column(
        "projects",
        sa.Column("provider", sa.String(50), nullable=True)
    )
    op.add_column(
        "projects",
        sa.Column("model", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects",
        sa.Column("generation_time", sa.Float(), nullable=True)
    )
    # Add indexes for better query performance
    op.create_index(op.f("ix_projects_folder_name"), "projects", ["folder_name"])
    op.create_index(op.f("ix_projects_created_at"), "projects", ["created_at"])
    op.create_index(op.f("ix_projects_updated_at"), "projects", ["updated_at"])


def downgrade() -> None:
    """Remove the added columns from projects table."""
    op.drop_index(op.f("ix_projects_updated_at"), table_name="projects")
    op.drop_index(op.f("ix_projects_created_at"), table_name="projects")
    op.drop_index(op.f("ix_projects_folder_name"), table_name="projects")
    op.drop_column("projects", "generation_time")
    op.drop_column("projects", "model")
    op.drop_column("projects", "provider")
