export function add_buttons(payload, BASE_URL, SESSION_ID) {
  const overlay = document.getElementById('overlay');
  overlay.innerHTML = '';

  if (!payload.elements) {
    overlay.style.display = 'none';
    return;
  }

  // Compute width and height
  let maxRow = 0;
  let maxCol = 0;
  for (const el of payload.elements) {
    const rowSpan = el.row_span || 1;
    const colSpan = el.column_span || 1;
    maxRow = Math.max(maxRow, el.row + rowSpan);
    maxCol = Math.max(maxCol, el.column + colSpan);
  }

  overlay.style.display = 'grid';
  overlay.style.gridTemplateColumns = `repeat(${maxCol}, 1fr)`;
  overlay.style.gridTemplateRows = `repeat(${maxRow}, 50px)`;
  overlay.style.gap = '5px';

  for (const el of payload.elements) {
    const cell = document.createElement(el.button_feedback !== null ? 'button' : 'div');
    cell.textContent = el.text;
    cell.className = 'grid-button';
    cell.style.gridColumn = `${el.column + 1} / span ${el.column_span || 1}`;
    cell.style.gridRow = `${el.row + 1} / span ${el.row_span || 1}`;

    if (el.button_feedback !== null) {
      cell.addEventListener('click', () => {
        overlay.style.display = 'none';  // 👈 Скрываем overlay
        fetch(`${BASE_URL}/command/${SESSION_ID}/command_button`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(el.button_feedback)
        });
      });
    } else {
      // Optional styling for plain text blocks
      cell.style.display = 'flex';
      cell.style.alignItems = 'center';
      cell.style.justifyContent = 'center';
      cell.style.background = '#ddd';
      cell.style.border = '1px solid #aaa';
    }

    overlay.appendChild(cell);
  }
}