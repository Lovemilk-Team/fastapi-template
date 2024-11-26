# Python FastAPI Template
> 这是一个 FastAPI 模板项目

## 版本需求
1. 兼容性保障: 3.10 <= Python <= 3.12 
2. 也许可以运行?: 3.9 <= Python < 3.10
3. 未经测试: 3 <= Python < 3.9
4. 别想了跑不起来: 2 <= Python < 3

## 部署
> 使用本模板视为已有 Python 基础, Git 基础 和 命令行操作 基础
1. 使用 `git clone` 本项目 或 在页面右上角 `Use this template > Create a new repository`
    ```shell
    git clone https://github.com/Lovemilk-Team/fastapi-template.git
    ```

2. 修改 `module_name` 文件夹名称 和 `run.py` 内的 `MODULE_NAME` 常量为 你项目的包名 (遵循 Python 包命名规则)

3. 按照 `config.py` 内各字段描述 (没有描述的参照给出链接内的文档) 修改各配置项的默认值, 或创建 `[dev.|prod.]config.y[a]ml` 按照 YAML 的对象格式 (键值对) 覆盖配置 <br>
   注意: 配置文件优先级为 `dev.config` > `prod.config` > `config`, 后缀名优先级为 `.yml` > `.yaml` > `.json` <br>
   > 越优先的配置的会覆盖不优先的配置 <br>
   > JSON 文件仍然将使用 YAML 加载器加载, 若需要在文件内注释请使用 `#` <br>
   > 以 `dev.` 开头的 配置文件 仅当环境变量 `MILK_DEVMODE` 为 `1` 时生效

4. 更改工作路径到项目目录
    ```shell
    cd fastapi-template/
    ```
5. 创建虚拟环境并安装依赖
   1. *nix
        ```shell
        python3 -m venv ./venv
        source ./venv/bin/activate 
        pip3 install -r requirements.txt
        ```
   2. Windows
        ```shell
        py -3 -m venv ./venv
        ./venv/Scripts/activate
        pip install -r requirements.txt
        ```

6. 运行 `run.py`
    ```shell
    python run.py
    ```
    > 要修改服务器的 host, port 配置, 请参见配置项 `app.host` 和 `app.port`, 默认使用 `127.0.0.1` 和 `8000`

## 开发须知
> 相对引入和绝对引入 "同一class" 不相等, 涉及导入本地模块请使用相对导入 (以 `.` 开头) <br>
> 服务器会在每次运行时 (除环境变量 `MILK_DEVMODE` 为 `1` 时外, 若已有生成文件则不会更新) 生成一个已合并的完整配置位于 `merged.config.yml` (部分字段由 Pydantic 处理生成为了 ISO 标准的字段)
1. 我们为您的服务器提供了一个统一的 `BaseResponse` 和 `ServerException`, 对于任何响应与异常, 请继承它们
2. 对于 `Rate Limit` 的支持 (参见配置项 `service.rate_limit`)
3. 我们为您提供了一个 loguru 的 logger (位于 `log.py` 的 `logger` 对象), 如需输出日志请使用该 logger <br>
   日志输出位于 `logs/<YYYY>-<MM>-<DD>.log`
4. 我们为您提供了一个统一的路由, 请在 `routers/` 下创建 py 文件并导出一个名为 `router` 的 `fastapi.APIRouter` 对象 (不导出则不会自动添加), 初始化时会自动导入并添加至 app `/`
5. 我们为您提供了一个统一的 `database` 初始化, 若需使用 database 的 session, 请使用 `.database.dbsession_depend` 的 FastAPI Depends <br>
   同时, 推荐在 `.database.structs` 定义 Model 和 Scheme, 若须在其他文件内定义必须在 `database/__init__.py` 中的 `engine = connect2database()` 行前导入
