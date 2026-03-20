import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",  # доступно со всех интерфейсов
        port=8000,       # порт по умолчанию
        reload=True      # автоматическая перезагрузка при изменении кода
    )