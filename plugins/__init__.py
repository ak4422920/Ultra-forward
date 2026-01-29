from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    # Professional response message
    return web.json_response("Forward Elite Bot is Running")

async def web_server():
    # Web application configuration
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
