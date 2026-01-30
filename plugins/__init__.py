from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    # Professional JSON Response for health checks
    return web.json_response({
        "status": "running",
        "bot": "Forward Elite V3",
        "version": "3.0.0",
        "secure": True
    })

async def web_server():
    # Web application configuration
    # client_max_size ko optimized rakha hai taaki memory leak na ho
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
