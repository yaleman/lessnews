FROM python:3.13 AS builder

#Set the working directory
WORKDIR /app

COPY pyproject.toml .
COPY README.md .

#copy all the files
RUN mkdir lessnews
COPY lessnews lessnews/

RUN python -m pip install .

FROM python:3.13-slim


COPY --from=builder /usr/local/bin/lessnews /usr/local/bin/lessnews
# COPY --from=builder /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

#Expose the required port
EXPOSE 8001

RUN mkdir /cache

ENV LESSNEWS_PORT=8001
ENV LESSNEWS_HOST=0.0.0.0
ENV LESSNEWS_CACHE_PATH=/cache

RUN useradd -M lessnewsuser
RUN chown -R lessnewsuser:lessnewsuser /cache
USER lessnewsuser

#Run the command
CMD ["lessnews"]

