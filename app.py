
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from streamlit_option_menu import option_menu

st.set_page_config(page_title="TMDB Movie Analytics", layout="wide")

st.title("🎬 TMDB Movie Analytics")

host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
user = "ap79ShHiJnSQWTa.root"
password = "3hr30YnebLaqaA89"
database = "TMDB"

url = URL.create(
    drivername="mysql+pymysql",
    username=user,
    password=password,
    host=host,
    port=4000,
    database=database
)

engine = create_engine(url)

# Load database tables
movies = pd.read_sql("SELECT * FROM movies", engine)
genres = pd.read_sql("SELECT * FROM genres", engine)
movie_genres = pd.read_sql("SELECT * FROM movie_genres", engine)
cast = pd.read_sql("SELECT * FROM `cast`", engine)

# Merge movie and genre data
movie_data = pd.merge(
    movies,
    movie_genres,
    on="movie_id"
)

movie_data = pd.merge(
    movie_data,
    genres,
    on="genre_id"
)

# Prepare release year
movie_data["release_date"] = pd.to_datetime(
    movie_data["release_date"],
    errors="coerce"
)

movie_data["release_year"] = movie_data["release_date"].dt.year

# Sidebar menu
with st.sidebar:

    selected = option_menu(
        "TMDB Analytics",
        ["Home", "Filters", "Dashboard", "Queries"],
        icons=["house", "filter", "bar-chart", "database"],
        menu_icon="cast",
        default_index=0
    )


# HOME PAGE
if selected == "Home":

    st.header("Welcome to TMDB Analytics")

    st.write(
        "Explore movie data using interactive filters, "
        "dashboards and SQL queries."
    )

    st.metric("Total Movies", movies["movie_id"].nunique())

    st.metric("Total Genres", genres["genre_id"].nunique())

    st.metric("Total Actors", cast["person_id"].nunique())


# FILTERS PAGE
elif selected == "Filters":

    st.header("Movie Filters")

    # Release year filter
    year_min = int(movie_data["release_year"].min())
    year_max = int(movie_data["release_year"].max())

    selected_year = st.slider(
        "Select Release Year",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max)
    )

    # Rating filter
    selected_rating = st.slider(
        "Minimum Movie Rating",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5
    )

    # Genre filter
    genre_list = sorted(
        movie_data["genre_name"].dropna().unique()
    )

    selected_genre = st.selectbox(
        "Select Genre",
        ["All"] + genre_list
    )

    # Language filter
    language_list = sorted(
        movie_data["original_language"].dropna().unique()
    )

    selected_language = st.selectbox(
        "Select Language",
        ["All"] + language_list
    )

    # Actor filter
    actor_list = sorted(
        cast["actor_name"].dropna().unique()
    )

    selected_actor = st.selectbox(
        "Select Actor",
        ["All"] + actor_list
    )

    # Budget filter
    budget_filter = st.checkbox(
        "Show only movies with Budget greater than 0",
        value=True
    )

    # Apply filters
    filtered_data = movie_data.copy()

    filtered_data = filtered_data[
        (filtered_data["release_year"] >= selected_year[0]) &
        (filtered_data["release_year"] <= selected_year[1]) &
        (filtered_data["vote_average"] >= selected_rating)
    ]

    if selected_genre != "All":

        filtered_data = filtered_data[
            filtered_data["genre_name"] == selected_genre
        ]

    if selected_language != "All":

        filtered_data = filtered_data[
            filtered_data["original_language"] == selected_language
        ]

    if budget_filter:

        filtered_data = filtered_data[
            filtered_data["budget"] > 0
        ]

    # Apply actor filter
    if selected_actor != "All":

        actor_movies = cast[
            cast["actor_name"] == selected_actor
        ]["movie_id"].unique()

        filtered_data = filtered_data[
            filtered_data["movie_id"].isin(actor_movies)
        ]

    # Remove duplicate movie rows
    filtered_data = filtered_data.drop_duplicates(
        subset="movie_id"
    )

    # Display movie count
    st.subheader("Filter Results")

    st.metric(
        "Matching Movies",
        filtered_data["movie_id"].nunique()
    )

    # Display movie data
    st.subheader("Filtered Movie Data")

    st.dataframe(
        filtered_data[
            [
                "movie_id",
                "title",
                "release_year",
                "genre_name",
                "original_language",
                "budget",
                "vote_average"
            ]
        ],
        use_container_width=True
    )



# DASHBOARD PAGE
elif selected == "Dashboard":

    st.title("TMDB Analytics")

    # KPI CARDS
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Movies", movies["movie_id"].nunique())
    col2.metric("Total Genres", genres["genre_id"].nunique())
    col3.metric("Total Actors", cast["person_id"].nunique())
    col4.metric("Average Rating", round(movies["vote_average"].mean(), 2))

    st.divider()

    # Prepare release year
    dashboard_data = movies.copy()

    dashboard_data["release_date"] = pd.to_datetime(
        dashboard_data["release_date"], errors="coerce"
    )

    dashboard_data["release_year"] = (
        dashboard_data["release_date"].dt.year
    )

    # Prepare correlation data
    numeric_data = dashboard_data[
        ["runtime", "budget", "revenue",
         "popularity", "vote_average", "vote_count"]
    ]

    # ROW 1 - HEATMAP AND LINE CHART
    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Correlation Heatmap")

        fig, ax = plt.subplots(figsize=(7, 5))

        sns.heatmap(
            numeric_data.corr(),
            annot=True,
            cmap="coolwarm",
            fmt=".2f",
            ax=ax
        )

        st.pyplot(fig)
        plt.close(fig)

    with col2:

        st.subheader("Movies Released per Year")

        year_count = dashboard_data.groupby(
            "release_year"
        )["movie_id"].nunique().dropna()

        fig, ax = plt.subplots(figsize=(7, 5))

        ax.plot(
            year_count.index,
            year_count.values,
            marker="o"
        )

        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Movies")
        ax.grid(True)

        st.pyplot(fig)
        plt.close(fig)

    st.divider()

    # ROW 2 - HISTOGRAM AND PIE CHART
    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Movie Rating Distribution")

        fig, ax = plt.subplots(figsize=(7, 5))

        sns.histplot(
            movies["vote_average"].dropna(),
            bins=20,
            kde=True,
            ax=ax
        )

        ax.set_xlabel("Movie Rating")
        ax.set_ylabel("Number of Movies")

        st.pyplot(fig)
        plt.close(fig)

    with col2:

        st.subheader("Genre Distribution")

        genre_data = movie_genres.merge(
            genres,
            on="genre_id"
        )

        genre_count = genre_data.groupby(
            "genre_name"
        )["movie_id"].nunique()

        fig, ax = plt.subplots(figsize=(7, 5))

        ax.pie(
            genre_count,
            labels=genre_count.index,
            autopct="%1.1f%%",
            startangle=90
        )

        st.pyplot(fig)
        plt.close(fig)

    st.divider()

    # ROW 3 - BAR CHART AND SCATTER PLOT
    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top 10 Movies by Revenue")

        top_movies = movies[
            movies["revenue"] > 0
        ].nlargest(10, "revenue")

        fig, ax = plt.subplots(figsize=(7, 5))

        sns.barplot(
            data=top_movies,
            x="revenue",
            y="title",
            ax=ax
        )

        ax.set_xlabel("Revenue")
        ax.set_ylabel("Movie")

        st.pyplot(fig)
        plt.close(fig)

    with col2:

        st.subheader("Budget vs Revenue")

        budget_data = movies[
            (movies["budget"] > 0) &
            (movies["revenue"] > 0)
        ]

        fig, ax = plt.subplots(figsize=(7, 5))

        sns.scatterplot(
            data=budget_data,
            x="budget",
            y="revenue",
            ax=ax
        )

        ax.set_xlabel("Budget")
        ax.set_ylabel("Revenue")

        st.pyplot(fig)
        plt.close(fig)


# QUERIES PAGE
elif selected == "Queries":

    # Select SQL question
    question = st.selectbox(
        "Select a SQL Query",
        [
            "Action movies released after 2015",
            "Top 10 highest-grossing movies",
            "Average budget and revenue by genre",
            "Top 10 actors by movie appearances",
            "Directors with more than 3 movies",
            "Top 10 most used keywords",
            "Movies with above-average budget and below-average revenue",
            "Actors in Christopher Nolan movies",
            "Highest-rated genre with at least 20 movies",
            "Top 10 movies with the most keywords"
        ]
    )

    # QUERY 1
    if question == "Action movies released after 2015":

        query = """
        SELECT DISTINCT
            m.title,
            m.release_date
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        WHERE g.genre_name = 'Action'
        AND YEAR(m.release_date) > 2015
        ORDER BY m.release_date
        """

        df = pd.read_sql(query, engine)

        st.subheader("Action Movies Released After 2015")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            df["release_year"] = pd.to_datetime(
                df["release_date"]
            ).dt.year

            chart_data = df.groupby(
                "release_year"
            ).size()

            st.subheader("Action Movies by Release Year")
            st.bar_chart(chart_data)

    # QUERY 2
    elif question == "Top 10 highest-grossing movies":

        query = """
        SELECT
            m.title,
            m.revenue,
            GROUP_CONCAT(DISTINCT g.genre_name) AS genres
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        WHERE m.revenue > 0
        GROUP BY m.movie_id, m.title, m.revenue
        ORDER BY m.revenue DESC
        LIMIT 10
        """

        df = pd.read_sql(query, engine)

        st.subheader("Top 10 Highest-Grossing Movies")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Movie Revenue Comparison")

            chart_data = df.set_index("title")["revenue"]
            st.bar_chart(chart_data)

    # QUERY 3
    elif question == "Average budget and revenue by genre":

        query = """
        SELECT
            g.genre_name,
            AVG(m.budget) AS average_budget,
            AVG(m.revenue) AS average_revenue
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        WHERE m.budget > 0 AND m.revenue > 0
        GROUP BY g.genre_name
        ORDER BY average_revenue DESC
        """

        df = pd.read_sql(query, engine)

        st.subheader("Average Budget and Revenue by Genre")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Budget vs Revenue by Genre")

            chart_data = df.set_index("genre_name")[
                ["average_budget", "average_revenue"]
            ]

            st.bar_chart(chart_data)


    # QUERY 4
    elif question == "Top 10 actors by movie appearances":

        query = """
        SELECT
            actor_name,
            COUNT(DISTINCT movie_id) AS movie_count
        FROM `cast`
        GROUP BY actor_name
        ORDER BY movie_count DESC
        LIMIT 10
        """

        df = pd.read_sql(query, engine)

        st.subheader("Top 10 Actors")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Actor Movie Appearances")

            chart_data = df.set_index("actor_name")["movie_count"]
            st.bar_chart(chart_data)


    # QUERY 5
    elif question == "Directors with more than 3 movies":

        query = """
        SELECT
            person_name AS director_name,
            COUNT(DISTINCT movie_id) AS movie_count
        FROM crew
        WHERE LOWER(job) = 'director'
        GROUP BY person_id, person_name
        HAVING COUNT(DISTINCT movie_id) > 3
        ORDER BY movie_count DESC
        """

        df = pd.read_sql(query, engine)

        st.subheader("Directors with More Than 3 Movies")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Director Movie Count")

            chart_data = df.set_index("director_name")["movie_count"]
            st.bar_chart(chart_data)


    # QUERY 6
    elif question == "Top 10 most used keywords":

        query = """
        SELECT
            keyword_name,
            COUNT(DISTINCT movie_id) AS movie_count
        FROM movie_keywords
        GROUP BY keyword_id, keyword_name
        ORDER BY movie_count DESC
        LIMIT 10
        """

        df = pd.read_sql(query, engine)

        st.subheader("Top 10 Movie Keywords")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Most Frequently Used Keywords")

            chart_data = df.set_index("keyword_name")["movie_count"]
            st.bar_chart(chart_data)


    # QUERY 7
    elif question == "Movies with above-average budget and below-average revenue":

        query = """
        SELECT
            title,
            budget,
            revenue
        FROM movies
        WHERE budget > (
            SELECT AVG(budget)
            FROM movies
            WHERE budget > 0
        )
        AND revenue < (
            SELECT AVG(revenue)
            FROM movies
            WHERE revenue > 0
        )
        AND revenue > 0
        ORDER BY budget DESC
        """

        df = pd.read_sql(query, engine)

        st.subheader("Above-Average Budget and Below-Average Revenue")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Budget vs Revenue")

            fig, ax = plt.subplots(figsize=(8, 5))

            sns.scatterplot(
                data=df,
                x="budget",
                y="revenue",
                ax=ax
            )

            ax.set_xlabel("Budget")
            ax.set_ylabel("Revenue")

            st.pyplot(fig)
            plt.close(fig)

    # QUERY 8
    elif question == "Actors in Christopher Nolan movies":

        query = """
        SELECT
            c.actor_name,
            COUNT(DISTINCT c.movie_id) AS movie_count
        FROM `cast` c
        JOIN crew cr ON c.movie_id = cr.movie_id
        WHERE LOWER(cr.job) = 'director'
        AND cr.person_name = 'Christopher Nolan'
        GROUP BY c.actor_name
        ORDER BY movie_count DESC, c.actor_name
        """

        df = pd.read_sql(query, engine)

        st.subheader("Actors in Christopher Nolan Movies")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Actor Appearances")

            chart_data = df.set_index("actor_name")["movie_count"]
            st.bar_chart(chart_data)

    # QUERY 9
    elif question == "Highest-rated genre with at least 20 movies":

        query = """
        SELECT
            g.genre_name,
            AVG(m.vote_average) AS average_rating,
            COUNT(DISTINCT m.movie_id) AS movie_count
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        WHERE m.vote_average > 0
        GROUP BY g.genre_id, g.genre_name
        HAVING COUNT(DISTINCT m.movie_id) >= 20
        ORDER BY average_rating DESC
        LIMIT 10
        """

        df = pd.read_sql(query, engine)

        st.subheader("Highest-Rated Genres")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Average Rating by Genre")

            chart_data = df.set_index("genre_name")["average_rating"]
            st.bar_chart(chart_data)


    # QUERY 10
    elif question == "Top 10 movies with the most keywords":

        query = """
        SELECT
            m.title,
            COUNT(mk.keyword_id) AS keyword_count
        FROM movies m
        JOIN movie_keywords mk ON m.movie_id = mk.movie_id
        GROUP BY m.movie_id, m.title
        ORDER BY keyword_count DESC
        LIMIT 10
        """

        df = pd.read_sql(query, engine)

        st.subheader("Top 10 Movies by Keyword Count")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.subheader("Number of Keywords per Movie")

            chart_data = df.set_index("title")["keyword_count"]
            st.bar_chart(chart_data)
