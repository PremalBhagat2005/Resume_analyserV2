import sys
print("Starting app...", file=sys.stdout, flush=True)

from app.factory import create_app

print("Creating app...", file=sys.stdout, flush=True)
app = create_app()
print("App created successfully!", file=sys.stdout, flush=True)

if __name__ == "__main__":
    print("Running Flask...", file=sys.stdout, flush=True)
    app.run(debug=True, host='0.0.0.0')
