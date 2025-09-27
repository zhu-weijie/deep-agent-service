# ---- Base Stage ----
# Use the official Python slim image as a base.
FROM python:3.11-slim AS base

# Set environment variables.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_NO_INTERACTION=1

# Install poetry.
RUN pip install poetry


# ---- Builder Stage ----
# This stage installs the Python dependencies into the system's site-packages.
FROM base AS builder

# Set the working directory.
WORKDIR /app

# Configure Poetry to NOT create a virtual environment.
# This ensures packages are installed in a globally accessible location.
RUN poetry config virtualenvs.create false

# Copy only the files needed for dependency installation.
COPY poetry.lock pyproject.toml ./

# Install only production dependencies into the system site-packages.
RUN poetry install --without dev --no-root --no-ansi


# ---- Final Application Stage ----
# This is the final, lean image for production.
FROM python:3.11-slim AS final

# Create a non-root user and group for security.
RUN addgroup --system app && adduser --system --group app

# Set the working directory.
WORKDIR /app

# Copy the installed dependencies from the builder stage.
# The executables are in /usr/local/bin and packages are in /usr/local/lib/...
COPY --from=builder /usr/local /usr/local

# Copy the application source code.
COPY ./src/app ./app

# Ensure the new user owns the application files.
RUN chown -R app:app /app

# Switch to the non-root user.
USER app

# Expose the port the app will run on.
EXPOSE 8000

# Command to run the application using uvicorn.
# /usr/local/bin is already on the default PATH.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
