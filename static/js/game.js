document.addEventListener('DOMContentLoaded', (event) => {
    isUpdating = false; // Ensure it's false at the start
    attachDragAndDropEventListeners();

    // Reset the game state when the page loads
    resetGame();

    // Fetch and render the initial board state
    setTimeout(function() {
        fetchNewBoardState();
    }, 1000); // Delay of 1 millisecond
});

let lastMove = null;

const PIECE_TO_SVG = {
    'bp': '/static/svg/pieces/bp.svg', // Black Pawn
    'br': '/static/svg/pieces/br.svg', // Black Rook
    'bn': '/static/svg/pieces/bn.svg', // Black Knight
    'bb': '/static/svg/pieces/bb.svg', // Black Bishop
    'bq': '/static/svg/pieces/bq.svg', // Black Queen
    'bk': '/static/svg/pieces/bk.svg', // Black King
    'wp': '/static/svg/pieces/wp.svg', // White Pawn
    'wr': '/static/svg/pieces/wr.svg', // White Rook
    'wn': '/static/svg/pieces/wn.svg', // White Knight
    'wb': '/static/svg/pieces/wb.svg', // White Bishop
    'wq': '/static/svg/pieces/wq.svg', // White Queen
    'wk': '/static/svg/pieces/wk.svg'  // White King
};

function isCastlingAttempt(pieceCode, fromPosition, toPosition) {
    if (pieceCode !== 'wk' && pieceCode !== 'bk') {
        return false;
    }

    // Check if the move is two squares horizontally
    return Math.abs(getColumnIndex(fromPosition) - getColumnIndex(toPosition)) === 2;
}

function getColumnIndex(position) {
    // Convert the column part of the position to an index, assuming position is like "e2"
    return position.charCodeAt(0) - 'a'.charCodeAt(0);
}

function sendCastlingAttemptToServer(fromPosition, toPosition, pieceCode) {
    fetch('/attempt_castle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: fromPosition, to: toPosition, piece: pieceCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBoard(data.newBoardState);
            updateGameMoves(data.gameMoves);
        } else {
            console.log('Castling attempt failed:', data.message);
        }
    })
    .catch(error => console.error('Error sending castling attempt to server:', error));
}

function attachDragAndDropEventListeners() {
    document.querySelectorAll('.chess-piece').forEach(piece => {
        piece.addEventListener('dragstart', handleDragStart);
        piece.addEventListener('dragend', handleDragEnd);
    });

    document.querySelectorAll('.square').forEach(square => {
        square.addEventListener('dragover', handleDragOver);
        square.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    this.style.opacity = '0.5';
    draggedItem = this;
    e.dataTransfer.setData('text/plain', this.id);
}

function handleDragEnd(e) {
    this.style.opacity = '';
}

function handleDragOver(e) {
    e.preventDefault();
}

let isUpdating = false;

async function handleDrop(e) {
    e.preventDefault();
    if (isUpdating) {
        console.log('Update in progress, move ignored');
        return;
    }

    isUpdating = true;
    const targetSquare = e.target.closest('.square');
    const fromPosition = draggedItem.parentElement.getAttribute('data-pos');
    const toPosition = targetSquare.getAttribute('data-pos');
    const pieceCode = draggedItem.id;

    console.log(`Dragged from ${fromPosition} to ${toPosition}`);

    if (fromPosition === toPosition) {
        console.log('Move to the same square, move ignored');
        isUpdating = false;
        return;
    }

    let isCapture = false;
    let isEnPassant = false;

    // Check if the move is a castling attempt
    if (isCastlingAttempt(pieceCode, fromPosition, toPosition)) {
        sendCastlingAttemptToServer(fromPosition, toPosition, pieceCode);
    }

    // Check for potential en passant move
    if (pieceCode[1] === 'p') {
        console.log('Checking for en passant...');
        const fromRow = parseInt(fromPosition[1], 10);
        const toRow = parseInt(toPosition[1], 10);
        const fromCol = columnIndex(fromPosition);
        const toCol = columnIndex(toPosition);

        console.log(`Pawn move from row ${fromRow} to row ${toRow}, column ${fromCol} to ${toCol}`);

        if (lastMove && lastMove.pieceCode[1] === 'p' && lastMove.pieceCode[0] !== pieceCode[0]) {
            const lastMoveFromRow = parseInt(lastMove.fromPosition[1], 10);
            const lastMoveToRow = parseInt(lastMove.toPosition[1], 10);
            const lastMoveToCol = columnIndex(lastMove.toPosition);

            console.log(`Last move: Pawn from row ${lastMoveFromRow} to row ${lastMoveToRow}, column ${lastMoveToCol}`);

            const correctRowBehind = (pieceCode.startsWith('w') && toRow === lastMoveToRow + 1) || (pieceCode.startsWith('b') && toRow === lastMoveToRow - 1);

            console.log(`Condition 3 (Current pawn is moving to the row directly behind the last move pawn): ${correctRowBehind}`);
            console.log(`Condition 4 (Current pawn is moving diagonally): ${Math.abs(toCol - fromCol) === 1}`);
            console.log(`Condition 5 (Destination square is empty): ${!targetSquare.querySelector('.chess-piece')}`);

            const isCorrectRowForEnPassant = (pieceCode.startsWith('w') && toRow === 6) || (pieceCode.startsWith('b') && toRow === 3);

            if (Math.abs(lastMoveFromRow - lastMoveToRow) === 2 && lastMoveToCol === toCol && isCorrectRowForEnPassant && Math.abs(toCol - fromCol) === 1 && !targetSquare.querySelector('.chess-piece')) {
                isEnPassant = true;
                isCapture = true;
                console.log('En passant move detected');
            } else {
                console.log('En passant conditions not met');
            }
        } else {
            console.log('Last move not by a pawn - en passant not possible');
        }
    }

    try {
        const isValidMove = await sendMoveToServer(fromPosition, toPosition, pieceCode, isCapture, isEnPassant);
        if (isValidMove) {
            // Update board for standard captures
            if (isCapture && !isEnPassant) {
                const capturedPiece = targetSquare.querySelector('.chess-piece');
                if (capturedPiece) {
                    console.log("Piece captured");
                    updateTakenPieceCount(capturedPiece);
                    capturedPiece.remove();
                }
            }

            // Update board for en passant captures
            if (isEnPassant) {
                const lastMoveToCol = columnIndex(lastMove.toPosition);
                const lastMoveFromRow = parseInt(lastMove.fromPosition[1], 10);
                const capturedPawnSquare = document.querySelector(`.square[data-pos="${String.fromCharCode('a'.charCodeAt(0) + lastMoveToCol)}${lastMoveFromRow}"]`);
                if (capturedPawnSquare) {
                    const capturedPawn = capturedPawnSquare.querySelector('.chess-piece');
                    if (capturedPawn) {
                        updateTakenPieceCount(capturedPawn);
                        capturedPawn.remove();
                    }
                }
            }

            // Update the position of the moved piece
            // (Your logic for updating the piece's position on the board)
        } else {
            console.log('Invalid move, piece not moved');
            draggedItem.parentElement.appendChild(draggedItem);
        }
    } catch (error) {
        console.log('Error processing move', error);
    } finally {
        isUpdating = false;
    }
}


function columnIndex(pos) {
    return pos.charCodeAt(0) - 'a'.charCodeAt(0);
}

function updateTakenPiecesDisplay(capturedPieces) {
    const unicodePieces = {
        'wp': '♙', 'bp': '♟',
        'wr': '♖', 'br': '♜',
        'wn': '♘', 'bn': '♞',
        'wb': '♗', 'bb': '♝',
        'wq': '♕', 'bq': '♛',
        'wk': '♔', 'bk': '♚'
    };

    // Function to update display for a single piece
    function updatePieceDisplay(pieceCode, containerId) {
        const pieceType = unicodePieces[pieceCode];
        const capturedContainer = document.getElementById(containerId);
        let pieceElement = capturedContainer.querySelector(`.captured-${pieceCode}`);

        if (!pieceElement) {
            pieceElement = document.createElement('div');
            pieceElement.className = `captured-${pieceCode}`;
            pieceElement.innerHTML = `${pieceType} x1`;
            capturedContainer.appendChild(pieceElement);
        } else {
            let currentCount = parseInt(pieceElement.textContent.split('x')[1]);
            pieceElement.innerHTML = `${pieceType} x${currentCount + 1}`;
        }
    }

    // Update display for white pieces
    capturedPieces.white.forEach(pieceCode => {
        updatePieceDisplay(pieceCode, 'white-captured-pieces');
    });

    // Update display for black pieces
    capturedPieces.black.forEach(pieceCode => {
        updatePieceDisplay(pieceCode, 'black-captured-pieces');
    });
}



function updateGameMoves(pgnMoves) {
    const movesContainer = document.getElementById('pgnMoves');
    movesContainer.textContent = pgnMoves;
}

function sendMoveToServer(fromPosition, toPosition, pieceCode, isCapture, isEnPassant) {
    return new Promise((resolve, reject) => {
        fetch('/record_move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from: fromPosition, to: toPosition, piece: pieceCode, capture: isCapture, enPassant: isEnPassant })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateBoard(data.newBoardState); // Update the chess board
                updateGameMoves(data.gameMoves); // Update the game moves display

                // Clear previous display of captured pieces
                document.getElementById('white-captured-pieces').innerHTML = '';
                document.getElementById('black-captured-pieces').innerHTML = '';

                // Update the display of captured pieces
                updateTakenPiecesDisplay(data.takenPieces);

                lastMove = { fromPosition, toPosition, pieceCode }; // Update last move
                resolve(true);
            } else {
                console.log('Invalid move:', data.message);
                resolve(false);
            }
        })
        .catch(error => {
            console.error('Error sending move to server:', error);
            reject(error);
        });
    });
}


function resetGame() {
    fetch('/reset_game', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBoard(data.newBoardState);
            updateGameMoves(data.gameMoves);
            document.getElementById('white-captured-pieces').innerHTML = '';
            document.getElementById('black-captured-pieces').innerHTML = '';
            isUpdating = false;
        }
    })
    .catch(error => console.error('Error during game reset:', error));
    isUpdating = false;
}

document.getElementById('resetGame').addEventListener('click', resetGame);

function fetchNewBoardState() {
    fetch('/get_current_board')
    .then(response => response.json())
    .then(boardState => {
        updateBoard(boardState);
    })
    .catch(error => console.error('Error fetching new board state:', error));
}

function copyPgnToClipboard() {
    const pgnString = document.getElementById('pgnMoves').textContent;
    navigator.clipboard.writeText(pgnString).then(() => {
        const copyButton = document.getElementById('copyPgn');
        const originalText = copyButton.textContent;
        copyButton.textContent = 'Copied!';
        setTimeout(() => {
            copyButton.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Error in copying PGN:', err);
    });
}

document.getElementById('copyPgn').addEventListener('click', copyPgnToClipboard);


function updateBoard(boardState) {
    console.log("Updating board state with:", boardState);

    // Clear existing pieces from all squares
    document.querySelectorAll('.square').forEach(square => {
        console.log("Clearing square:", square.getAttribute('data-pos'));
        while (square.firstChild) {
            console.log("Removing child:", square.firstChild);
            square.removeChild(square.firstChild);
        }
    });

    // Iterate over the boardState array and update each square
    for (let i = 0; i < 8; i++) {
        for (let j = 0; j < 8; j++) {
            const pieceCode = boardState[i][j];
            const rowNumber = 8 - i; // Convert array index to chessboard row number
            const colLetter = 'abcdefgh'[j]; // Convert array index to chessboard column letter
            const squareSelector = `.square[data-pos="${colLetter}${rowNumber}"]`;
            const square = document.querySelector(squareSelector);

            if (!square) {
                console.error("Could not find square:", squareSelector);
                continue;
            }

            console.log(`Processing square at ${colLetter}${rowNumber} for piece ${pieceCode}`);

            // Add a new piece if needed
            if (pieceCode && PIECE_TO_SVG.hasOwnProperty(pieceCode)) {
                console.log(`Adding piece ${pieceCode} to square at ${colLetter}${rowNumber}`);
                const imgElement = document.createElement('img');
                imgElement.src = PIECE_TO_SVG[pieceCode];
                imgElement.className = 'chess-piece';
                imgElement.draggable = true;
                imgElement.id = pieceCode;
                square.appendChild(imgElement);
            } else {
                console.log(`No piece or invalid piece code at ${colLetter}${rowNumber}.`);
            }
        }
    }

    attachDragAndDropEventListeners();
}


function fetchNewBoardState() {
    fetch('/get_current_board')
    .then(response => response.json())
    .then(boardState => {
        updateBoard(boardState); // Update the board with the new state
    })
    .catch(error => console.error('Error fetching new board state:', error));
}
