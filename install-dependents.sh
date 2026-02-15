#!/bin/sh
npm install
npm run preview-build

cd daemon
npm install
cd ../panel
npm install
cd ../frontend
npm install

echo ""
echo "Installing Python dependencies for tunnel manager..."
cd ..

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "Warning: Python not found! Skipping tunnel manager dependencies."
    echo "Please install Python 3.7+ to use the tunnel manager feature."
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ]; then
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install -r requirements.txt
    echo "Python dependencies installed successfully!"
fi

echo "------------"
echo "All done!"
echo "------------"
