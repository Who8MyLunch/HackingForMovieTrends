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

Very early this morning I could not sleep as I kept thinking about this effort.  I kept reviewing in
my head details of the objective in the section above.  I need a way to make sense of text
describing a movie.  A quick search on Github turned up this great Python package:
[TextBlob](https://github.com/sloria/TextBlob).  The text from the website says:

    A library for processing textual data. It provides a simple API for diving into common natural
    language processing (NLP) tasks such as part-of-speech tagging, noun phrase extraction,
    sentiment analysis, classification, translation, and more.

Behind the scenes it uses [NLTK](http://www.nltk.org/) and
[patterns](http://www.clips.ua.ac.be/pages/pattern-en).  I've never done anything significant with
text processing.  This tools is a great place to start!


[The OMDb API](http://www.omdbapi.com/)

[Sequel Movies 2012](http://www.movieinsider.com/movies/sequel/2012)
