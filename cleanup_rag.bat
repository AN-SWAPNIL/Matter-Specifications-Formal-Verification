@echo off
echo ========================================
echo Cleaning up old RAG database...
echo ========================================
echo.

if exist tamarin_vectordb (
    echo Removing tamarin_vectordb directory...
    rmdir /s /q tamarin_vectordb
    echo   - Vector database removed
) else (
    echo   - No vector database found
)

if exist ingestion_log.json (
    echo Removing ingestion_log.json...
    del /q ingestion_log.json
    echo   - Ingestion log removed
) else (
    echo   - No ingestion log found
)

echo.
echo ========================================
echo Cleanup complete!
echo ========================================
echo.
echo Next step: Run 'python tamarin_vector_ingestion.py' to rebuild the database
echo.
pause
