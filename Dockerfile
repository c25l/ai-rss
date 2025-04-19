FROM condaforge/miniforge3
WORKDIR /usr/src/app
COPY requirements.txt .
RUN conda install numpy pandas scipy scikit-learn networkx hdbscan
RUN pip install -r requirements.txt
COPY . .
CMD ["python","airss.py"]
