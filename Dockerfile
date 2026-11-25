FROM astral/uv:python3.12-bookworm-slim


# 2. Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy and install dependencies first to leverage Docker layer caching
COPY requirements.txt .
COPY pyproject.toml .
RUN uv sync

# 5. Copy the rest of your application code into the container
COPY . .
RUN uv run pyinstaller --clean --onefile --console --name main main.py
# 6. Specify the command to run your application
CMD ["./dist/morphai"]