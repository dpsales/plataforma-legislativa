'use strict';

(function () {
  const selectElement = document.getElementById('id_organs');
  if (!selectElement) return;

  // Enable multiple selection with keyboard shortcuts
  let lastSelected = null;
  
  selectElement.addEventListener('mousedown', function(e) {
    if (e.target.tagName !== 'OPTION') return;
    
    e.preventDefault();
    
    const option = e.target;
    const selectedOptions = Array.from(selectElement.selectedOptions);
    const allOptions = Array.from(selectElement.options);
    
    // Ctrl/Cmd click - toggle single option
    if (e.ctrlKey || e.metaKey) {
      option.selected = !option.selected;
      lastSelected = option;
    }
    // Shift click - select range
    else if (e.shiftKey && lastSelected) {
      const start = allOptions.indexOf(lastSelected);
      const end = allOptions.indexOf(option);
      const [low, high] = start < end ? [start, end] : [end, start];
      
      for (let i = low; i <= high; i++) {
        allOptions[i].selected = true;
      }
    }
    // Regular click - select single (clear others)
    else {
      selectedOptions.forEach(opt => opt.selected = false);
      option.selected = true;
      lastSelected = option;
    }
    
    selectElement.dispatchEvent(new Event('change', { bubbles: true }));
  });
  
  // Allow keyboard navigation to work properly
  selectElement.addEventListener('keydown', function(e) {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      const focused = selectElement.options[selectElement.selectedIndex];
      if (focused) {
        focused.selected = !focused.selected;
        selectElement.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  });
})();
