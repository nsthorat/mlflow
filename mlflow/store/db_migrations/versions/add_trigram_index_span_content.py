"""add trigram index for span content search

Revision ID: add_trigram_index_span_content
Revises: a1b2c3d4e5f6
Create Date: 2025-08-04 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "add_trigram_index_span_content"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # Get the database dialect
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        # Check if pg_trgm extension is installed
        result = bind.execute(
            sa.text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
        )
        has_pg_trgm = result.scalar()

        if has_pg_trgm:
            # Create the trigram index
            op.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_content_trgm "
                "ON spans USING gin (content gin_trgm_ops)"
            )
        else:
            context.get_context().config.print_stdout(
                "\n⚠️  PostgreSQL pg_trgm extension not found. "
                "To enable span.content search optimization, run:\n"
                "    CREATE EXTENSION IF NOT EXISTS pg_trgm;\n"
                "Then re-run this migration."
            )


def downgrade():
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_spans_content_trgm")
