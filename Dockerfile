# ---- Base Stage ----
# Use the official Python slim image as a base.
FROM python:3.11-slim AS base

# Set environment variables to prevent writing .pyc files and to ensure output is unbuffered.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install poetry.
RUN pip install poetry


# ---- Builder Stage ----
# This stage installs the Python dependencies.
FROM base AS builder

# Set the working directory.
WORKDIR /app

# Copy only the files needed for dependency installation.
# This leverages Docker's layer caching.
COPY poetry.lock pyproject.toml ./

# Install dependencies using Poetry, without creating a virtual environment inside the container.
# --no-dev installs only production dependencies.
RUN poetry install --no-dev --no-interaction --no-ansi


# ---- Final Application Stage ----
# This is the final, lean image for production.
FROM base AS final

# Create a non-root user and group for security.
RUN addgroup --system app && adduser --system --group app

# Set the working directory.
WORKDIR /app

# Copy the installed dependencies from the builder stage.
COPY --from=builder /root/.local /root/.local

# Copy the application source code.
COPY ./src/app ./app

# Ensure the new user owns the application files.
RUN chown -R app:app /app

# Switch to the non-root user.
USER app

# Expose the port the app will run on.
EXPOSE 8000

# Set the path to include the installed Python packages.
ENV PATH="/root/.local/bin:$PATH"

# Command to run the application using uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
