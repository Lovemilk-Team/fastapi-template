from module_name.shared import config

if __name__ == '__main__':
    from uvicorn import run
    run(
        # WARNING:  You must pass the application as an import string to enable 'reload' or 'workers'.
        f'{config.app.module_name}.app:app',
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        reload_dirs=[f'./{config.app.module_name}', './frontend'],
        proxy_headers=config.app.proxy_headers
    )
