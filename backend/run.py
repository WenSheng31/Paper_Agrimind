import os
import uvicorn

if __name__ == "__main__":
    reload = os.environ.get('reload', 'False').lower() == 'true'

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",             
        port=8000,
        reload=reload,               
        proxy_headers=True,        
        forwarded_allow_ips="*"     
    )
