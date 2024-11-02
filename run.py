MODULE_NAME = 'module_name'

# import {MODULE_NAME}.shared
# config = {MODULE_NAME}.shared.config
config = __import__(f'{MODULE_NAME}.shared').shared.config

if __name__ == '__main__':
    from uvicorn import run
    run(
        # WARNING:  You must pass the application as an import string to enable 'reload' or 'workers'.
        f'{MODULE_NAME}.app:app',
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        reload_dirs=[f'./{MODULE_NAME}'],
        proxy_headers=config.app.proxy_headers
    )
