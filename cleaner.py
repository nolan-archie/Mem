import os

import tokenize



PROJECT_ROOT = "."                                              

BACKUP_SUFFIX = ".bak"



def remove_comments_from_file(filepath):

    backup_path = filepath + BACKUP_SUFFIX

    os.rename(filepath, backup_path)                   



    with open(backup_path, "rb") as f_in, open(filepath, "w", encoding="utf-8") as f_out:

        tokens = tokenize.tokenize(f_in.readline)

        prev_end = (1, 0)

        for tok in tokens:

            if tok.type == tokenize.COMMENT or tok.type == tokenize.ENCODING:

                continue

            (srow, scol) = tok.start

            (erow, ecol) = tok.end

                                                        

            if prev_end[0] < srow:

                f_out.write("\n" * (srow - prev_end[0]))

                f_out.write(" " * scol)

            else:

                f_out.write(" " * (scol - prev_end[1]))

            f_out.write(tok.string)

            prev_end = (erow, ecol)



def remove_comments_recursive(root_dir):

    for dirpath, _, filenames in os.walk(root_dir):

        for fname in filenames:

            if fname.endswith(".py"):

                file_path = os.path.join(dirpath, fname)

                try:

                    remove_comments_from_file(file_path)

                    print(f"Cleaned: {file_path}")

                except Exception as e:

                    print(f"Failed: {file_path} -> {e}")



if __name__ == "__main__":

    remove_comments_recursive(PROJECT_ROOT)

