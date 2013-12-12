Notes
=====

Objective
---------

My objective for this morning’s effort is to demonstrate my data processing and analysis
capabilities outside of my tradiational hyperspectral remote sensing work.  I have played in that
arena for a long time and picked up a good number of modeling and analysis skills.  This present
effort is meant to be a quick example of processing unfamiliar data using new tools and protocols.
This work needs to be quick, efficient, and have a clear punch line.

I made a statement a few days ago that I would like to solve new types of problems.  Foe example, I
might treat a new movie as a collection of word feature vectors pulled out of a Twitter feed.  I
would then make statistical associations with other movies having known performance characteristics
such as viewer retention and engagement.  The validity of the association process could be verified
by testing with lablled data.  Results from such a process might be useful for someones planning
efforts.

Early Morning Thinking
----------------------

Very early this morning I could not sleep as I kept thinking about this effort.  I kept reviewing
in my head details of the objective in the section above.  I need a way to make sense of text
describing a movie.  A quick search on Github turned up this great Python package:
[TextBlob](https://github.com/sloria/TextBlob).  The text from the website says:

    A library for processing textual data. It provides a simple API for diving into common natural
    language processing (NLP) tasks such as part-of-speech tagging, noun phrase extraction,
    sentiment analysis, classification, translation, and more.

Behind the scenes it uses [NLTK](http://www.nltk.org/) and
[patterns](http://www.clips.ua.ac.be/pages/pattern-en).  I've have not done much with natural
language text processing.  This tools will be a great place to start!

I found a nice web API for querrying information from IMDb and RottenTomatoes:
[The OMDb API](http://www.omdbapi.com/).  For example, this query for information about the movie
Star Wars, `http://www.omdbapi.com/?s=Star%20Wars1` yields this JSON response:

    {"Search": [{"Title": "Star Wars", "Year": "1977",
                 "imdbID": "tt0076759", "Type": "movie"},
                {"Title": "Star Wars: Episode V - The Empire Strikes Back", "Year": "1980",
                 "imdbID": "tt0080684", "Type": "movie"},
                {"Title": "Star Wars: Episode VI - Return of the Jedi", "Year": "1983",
                 "imdbID": "tt0086190", "Type": "movie"},
                {"Title": "Star Wars: Episode I - The Phantom Menace", "Year": "1999",
                 "imdbID": "tt0120915", "Type": "movie"},
                {"Title": "Star Wars: Episode III - Revenge of the Sith", "Year": "2005",
                 "imdbID": "tt0121766", "Type": "movie"},
                {"Title": "Star Wars: Episode II - Attack of the Clones", "Year": "2002",
                 "imdbID": "tt0121765", "Type": "movie"},
                {"Title": "Star Wars: The Clone Wars", "Year": "2008",
                 "imdbID": "tt1185834", "Type": "movie"},
                {"Title": "Star Wars: The Clone Wars", "Year": "2008",
                "imdbID": "tt0458290", "Type": "series"},
                {"Title": "Star Wars: Clone Wars", "Year": "2003",
                 "imdbID": "tt0361243", "Type": "series"},
                {"Title": "The Star Wars Holiday Special", "Year": "1978",
                 "imdbID": "tt0193524", "Type": "movie"}]}

Its just a bit more work to also retrieve information from RottenTomatoes using the imdbID as a
reference number.

Next I wanted a list of intersting movies to play with.  I found this list of titles from 2012 for
sequels of popular movies: [Sequel Movies 2012](http://www.movieinsider.com/movies/sequel/2012).  I
figure I'll need to manipulate some of that data by hand just to get it done quickly.  I would
normally write some code, but right now this is a one-time deal.

