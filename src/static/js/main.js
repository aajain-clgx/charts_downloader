document.addEventListener('DOMContentLoaded', () => {
    const gallery = document.getElementById('gallery');
    const modal = document.getElementById('modal');
    const modalImage = document.getElementById('modal-image');
    const modalTicker = document.getElementById('modal-ticker');
    const modalDate = document.getElementById('modal-date');
    const modalTags = document.getElementById('modal-tags');
    const closeModal = document.querySelector('.close-modal');
    const addTagBtn = document.getElementById('add-tag-btn');
    const newTagInput = document.getElementById('new-tag-input');
    const applyFiltersBtn = document.getElementById('apply-filters');

    let currentChartId = null;

    // Fetch and display charts
    async function loadCharts() {
        const ticker = document.getElementById('filter-ticker').value;
        const dateStart = document.getElementById('filter-date-start').value;
        const dateEnd = document.getElementById('filter-date-end').value;
        const tag = document.getElementById('filter-tag').value;

        const params = new URLSearchParams();
        if (ticker) params.append('ticker', ticker);
        if (dateStart) params.append('date_start', dateStart);
        if (dateEnd) params.append('date_end', dateEnd);
        if (tag) params.append('tag', tag);

        const response = await fetch(`/api/charts?${params.toString()}`);
        const charts = await response.json();

        gallery.innerHTML = '';
        charts.forEach(chart => {
            const card = document.createElement('div');
            card.className = 'chart-card';

            const tagsHtml = chart.tags ? chart.tags.split(',').map(t => `<span class="tag-pill">${t}</span>`).join('') : '';

            card.innerHTML = `
                <img src="/images/${chart.image_filename}" class="chart-thumb" loading="lazy">
                <div class="chart-info">
                    <div class="chart-ticker">${chart.ticker}</div>
                    <div class="chart-date">${chart.chart_date}</div>
                    <div class="chart-tags">${tagsHtml}</div>
                </div>
            `;

            card.addEventListener('click', () => openModal(chart));
            gallery.appendChild(card);
        });
    }

    function openModal(chart) {
        currentChartId = chart.id;
        modalImage.src = `/images/${chart.image_filename}`;
        modalTicker.textContent = chart.ticker;
        modalDate.textContent = chart.chart_date;

        renderModalTags(chart.tags);

        modal.classList.remove('hidden');
    }

    function renderModalTags(tagsString) {
        modalTags.innerHTML = '';
        if (tagsString) {
            tagsString.split(',').forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag-pill';
                tagEl.textContent = tag;
                modalTags.appendChild(tagEl);
            });
        }
    }

    closeModal.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    applyFiltersBtn.addEventListener('click', loadCharts);

    // Add Tag
    addTagBtn.addEventListener('click', async () => {
        const tag = newTagInput.value.trim();
        if (!tag || !currentChartId) return;

        const response = await fetch('/api/tags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chart_id: currentChartId, tag_name: tag })
        });

        if (response.ok) {
            newTagInput.value = '';
            // Refresh current view logic - ideally we just update the DOM
            // For now, let's reload the charts to reflect changes
            loadCharts();

            // Also update the modal tags
            const currentTags = Array.from(modalTags.children).map(c => c.textContent);
            if (!currentTags.includes(tag)) {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag-pill';
                tagEl.textContent = tag;
                modalTags.appendChild(tagEl);
            }
        }
    });

    // Initial load
    loadCharts();
});
