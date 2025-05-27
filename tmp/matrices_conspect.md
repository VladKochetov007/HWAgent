**Conspect: Matrices in Linear Algebra**

**1. Definition:**
*   A matrix is a rectangular array of numbers, symbols, or expressions arranged in rows and columns.
*   The size or dimension of a matrix is given by the number of rows ($m$) and the number of columns ($n$), denoted as $m \times n$.
*   Elements of a matrix are typically denoted by $a_{ij}$, where $i$ is the row index and $j$ is the column index.

*Example:*
A $2\times3$ matrix:
$$
A = \begin{pmatrix}
 1 & 2 & 3 \\
 4 & 5 & 6
\end{pmatrix}
$$

**2. Matrix Operations:**

*   **Addition:**
    *   Matrices can be added if they have the same dimensions.
    *   Addition is performed by adding corresponding elements.
    *   $A + B = [a_{ij} + b_{ij}]$

    *Example:*
    $$
\begin{pmatrix}
 1 & 2 \\
 3 & 4
\end{pmatrix} + \begin{pmatrix}
 3 & 4 \\
 5 & 6
\end{pmatrix} = \begin{pmatrix}
 1+3 & 2+4 \\
 3+5 & 4+6
\end{pmatrix} = \begin{pmatrix}
 4 & 6 \\
 8 & 10
\end{pmatrix}
    $$

*   **Subtraction:**
    *   Matrices can be subtracted if they have the same dimensions.
    *   Subtraction is performed by subtracting corresponding elements.
    *   $A - B = [a_{ij} - b_{ij}]$

    *Example:*
    $$
\begin{pmatrix}
 4 & 6 \\
 8 & 10
\end{pmatrix} - \begin{pmatrix}
 1 & 2 \\
 3 & 4
\end{pmatrix} = \begin{pmatrix}
 4-1 & 6-2 \\
 8-3 & 10-4
\end{pmatrix} = \begin{pmatrix}
 3 & 4 \\
 5 & 6
\end{pmatrix}
    $$

*   **Scalar Multiplication:**
    *   Multiplying a matrix by a scalar ($c$) involves multiplying every element in the matrix by that scalar.
    *   $c \cdot A = [c \cdot a_{ij}]$

    *Example:*
    $$
2 \cdot \begin{pmatrix}
 1 & 2 \\
 3 & 4
\end{pmatrix} = \begin{pmatrix}
 2\cdot1 & 2\cdot2 \\
 2\cdot3 & 2\cdot4
\end{pmatrix} = \begin{pmatrix}
 2 & 4 \\
 6 & 8
\end{pmatrix}
    $$

*   **Matrix Multiplication:**
    *   Two matrices $A$ ($m \times n$) and $B$ ($p \times q$) can be multiplied if and only if the number of columns in $A$ is equal to the number of rows in $B$ ($n = p$).
    *   The resulting matrix $C$ will have the dimensions $m \times q$.
    *   The element $c_{ij}$ of the product matrix is the dot product of the $i$-th row of $A$ and the $j$-th column of $B$.

    *Example:*
    Let $A$ be a $2\times2$ matrix and $B$ be a $2\times2$ matrix:
$$
A = \begin{pmatrix}
 1 & 2 \\
 3 & 4
\end{pmatrix}, B = \begin{pmatrix}
 5 & 6 \\
 7 & 8
\end{pmatrix}
$$
$C = A \cdot B$

$C_{11} = (1 \cdot 5) + (2 \cdot 7) = 5 + 14 = 19$

$C_{12} = (1 \cdot 6) + (2 \cdot 8) = 6 + 16 = 22$

$C_{21} = (3 \cdot 5) + (4 \cdot 7) = 15 + 28 = 43$

$C_{22} = (3 \cdot 6) + (4 \cdot 8) = 18 + 32 = 50$

$$
C = \begin{pmatrix}
 19 & 22 \\
 43 & 50
\end{pmatrix}
    $$

**3. Special Types of Matrices:**

*   **Identity Matrix ($I$):**
    *   A square matrix (same number of rows and columns) with ones on the main diagonal (from top-left to bottom-right) and zeros elsewhere.
    *   When multiplied by any matrix $A$ (of compatible dimensions), it results in $A$ ($A \cdot I = I \cdot A = A$).

    *Example ($3\times3$ Identity Matrix):*
    $$
I = \begin{pmatrix}
 1 & 0 & 0 \\
 0 & 1 & 0 \\
 0 & 0 & 1
\end{pmatrix}
    $$

*   **Zero Matrix ($0$):**
    *   A matrix of any dimension filled with all zeros.
    *   When added to any matrix $A$ (of the same dimensions), it results in $A$ ($A + 0 = A$).

    *Example ($2\times3$ Zero Matrix):*
    $$
0 = \begin{pmatrix}
 0 & 0 & 0 \\
 0 & 0 & 0
\end{pmatrix}
    $$

*   **Transpose of a Matrix ($A^T$):**
    *   Obtained by flipping a matrix over its diagonal, switching the row and column indices of each element.
    *   If $A$ is an $m \times n$ matrix, its transpose $A^T$ is an $n \times m$ matrix.
    *   $(A^T)_{ij} = a_{ji}$

    *Example:*
    Let $A$ be a $2\times3$ matrix:
    $$
A = \begin{pmatrix}
 1 & 2 & 3 \\
 4 & 5 & 6
\end{pmatrix}
$$
    Its transpose $A^T$ is a $3\times2$ matrix:
    $$
A^T = \begin{pmatrix}
 1 & 4 \\
 2 & 5 \\
 3 & 6
\end{pmatrix}
    $$

This conspect covers the fundamental concepts and operations related to matrices in linear algebra.