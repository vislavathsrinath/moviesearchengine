// Show Search Results
document.getElementById("search-btn").addEventListener("click", () => {
  const query = document.getElementById("search-input").value;
  fetch(`/search?query=${query}`)
    .then(response => response.json())
    .then(movies => {
      const resultsDiv = document.getElementById("results");
      resultsDiv.innerHTML = ""; // Clear previous results

      if (movies.length > 0) {
        movies.forEach(movie => {
          const movieDiv = document.createElement("div");
          movieDiv.className = "movie";
          movieDiv.innerHTML = `
            <h3>${movie.title}</h3>
            <p>Genre: ${movie.genre}</p>
            <p>Release Date: ${movie.release_date}</p>
            <p>Director: ${movie.director}</p>
            <img src="${movie.poster_url}" alt="${movie.title} poster">
            <button onclick="addToWatchlist(${movie.id})">Add to Watchlist</button>
          `;
          resultsDiv.appendChild(movieDiv);
        });
      } else {
        resultsDiv.innerHTML = "<p>No movies found.</p>";
      }
    })
    .catch(err => console.error(err));
});

// Add Movie to Watchlist
function addToWatchlist(movieId) {
  fetch("/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ movie_id: movieId })
  })
  .then(response => response.json())
  .then(data => alert(data.message));
}

// Remove Movie from Watchlist
function removeFromWatchlist(movieId) {
  fetch("/watchlist", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ movie_id: movieId })
  })
  .then(response => response.json())
  .then(data => alert(data.message));
}

// Show Search History
document.getElementById("history-btn").addEventListener("click", () => {
  fetch('/history')
    .then(response => response.json())
    .then(history => {
      const historyDiv = document.getElementById("history");
      historyDiv.innerHTML = "";  // Clear previous history
      history.forEach(entry => {
        const entryDiv = document.createElement("div");
        entryDiv.innerHTML = `${entry.query} - ${entry.timestamp}`;
        historyDiv.appendChild(entryDiv);
      });
    });
});

// Clear Search History
document.getElementById("clear-history-btn").addEventListener("click", () => {
  fetch('/history', { method: 'DELETE' })
    .then(response => response.json())
    .then(data => alert(data.message));
});

// Show Watchlist
document.getElementById("watchlist-btn").addEventListener("click", () => {
  fetch('/watchlist')
    .then(response => response.json())
    .then(watchlist => {
      const watchlistDiv = document.getElementById("watchlist");
      watchlistDiv.innerHTML = "";  // Clear previous watchlist
      watchlist.forEach(movie => {
        const movieDiv = document.createElement("div");
        movieDiv.innerHTML = `
          <p>${movie.title}</p>
          <img src="${movie.poster_url}" alt="${movie.title} poster">
          <button onclick="removeFromWatchlist(${movie.movie_id})">Remove</button>
        `;
        watchlistDiv.appendChild(movieDiv);
      });
    });
});

// Toggle Dark Mode
document.getElementById("toggle-theme").addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
});
