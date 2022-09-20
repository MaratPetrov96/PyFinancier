from tkinter import *
from tkinter import font
from tkinter import ttk
from tkcalendar import Calendar,DateEntry
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

months_dict = {'01':'январь','02':'февраль','03':'март','04':'апрель','05':'май','06':'июнь'
 ,'07':'июль','08':'август','09':'сентябрь','10':'октябрь','11':'ноябрь','12':'декабрь'}

con = sqlite3.connect('Finances.sql') #подключение к файлу или его создание
types = [('Доход',),('Расход',)] #типы записей
types_ = [i[0] for i in types] #для добавления в БД

class App(Tk):

    def __init__(self):
        global FONT
        super().__init__() #инициализация графики
        self.protocol("WM_DELETE_WINDOW", self.quit_me)
        self.title('Финансовый учёт')
        FONT = font.Font(self,size = 20)
        self.setStyle() #создание стилей для кнопок
        self.geometry('1000x600') #размер окна
        self.cur = con.cursor() #курсор для команд на SQL
        try: #проверка существования таблицы TYPES
            self.cur.execute('SELECT * FROM TYPES')
        except:
            self.cur.execute('CREATE TABLE TYPES (id integer primary key, title varchar(10))')
            self.cur.executemany('''INSERT INTO TYPES (title) VALUES(?)''',types)
            con.commit()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS RECORDS
    (id integer primary key, summa real not null, descr text not null, date date not null,
    type integer not null, FOREIGN KEY (type) REFERENCES TYPES (id))''') #проверка существовани таблицы RECORDS
        self.cur.execute("SELECT DISTINCT strftime('%Y',date) as year from RECORDS order by year")
        self.years = [int(y[0]) for y in self.cur.fetchall()] #сохранение годов
        self.menu = Menu(self) #верхнее меню
        self.menu.add_command(label='Главная страница',command=self.main)
        self.menu.add_command(label='Добавить запись',command=self.add_form)
        self.menu.add_command(label='Доходы',command=lambda arg='Доход':self.show_records(arg))
        self.menu.add_command(label='Расходы',command=lambda arg='Расход':self.show_records(arg))
        self.menu.add_command(label='Статистика доходов',command=lambda arg='Доход':self.visual(arg))
        self.menu.add_command(label='Статистика расходов',command=lambda arg='Расход':self.visual(arg))
        self.menu.add_command(label='Статистика разницы',command=lambda arg='Прибыль/убыток':self.visual(arg))
        self.config(menu=self.menu) #добавление меню
        try: #установка года, проверяется, есть ли записи вообще
            self.current_year = self.years[-1]
        except:
            self.current_year = 0
        self.main() #главная страница

    def main(self):
        self.destroy_()
        Label(self,text='ПОСЛЕДНИЕ ОПЕРАЦИИ',font=FONT).grid(row=0,column=1)
        self.cur.execute('select * from RECORDS order by date desc limit 7') #id,summa,descr,date,type
        Label(self,text='\t',font=FONT).grid(row=0,column=0)
        for n,i in enumerate(self.cur.fetchall(),1):
            year,month,day = i[-2].split('-')
            if i[-1]-1:
                Label(self,text=f'{i[2]}\t\t-{i[1]} р.',font=FONT).grid(row=n*2-1,column=1)
            else:
                Label(self,text=f'{i[2]}\t\t{i[1]} р.',font=FONT).grid(row=n*2-1,column=1)
            Label(self,text=f'{day}.{month}.{year}',font=FONT).grid(row=n*2,column=1)

    def show_records(self,arg):
        self.destroy_()

        frame = Frame(self)
        frame.pack(fill=BOTH,expand=1)

        self.canvas = Canvas(frame)
        self.canvas.pack(side=LEFT,fill=BOTH,expand=1)

        scroll = Scrollbar(frame,orient="vertical",command=self.canvas.yview)
        scroll.pack(side=RIGHT,fill=Y)

        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.bind('<Configure>',lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        data_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window=data_frame,anchor='nw')

        self.cur.execute(f'''SELECT RECORDS.id,RECORDS.summa,RECORDS.descr,RECORDS.date
        from RECORDS JOIN TYPES on RECORDS.type=TYPES.id
        where TYPES.title ="{arg}" order by RECORDS.date DESC''')

        dct = dict() #словарь для агреггации данных
        #вид словаря: {год:{месяц:{число:[записи]}}}
        for i in self.cur.fetchall():
            year,month,day = i[-1].replace('-','\t-').split('-')
            if year not in dct.keys():
                dct[year] = dict()
            if month not in dct[year].keys():
                dct[year][month] = dict()
            if day not in dct[year][month].keys():
                dct[year][month][day] = []
            dct[year][month][day].append(i[:3])
        main_root = data_frame
        Label(main_root,text=f'{arg}ы',font=FONT).grid(row=0,column=1)
        for n,(year,months) in enumerate(dct.items()):
            year_frame = ttk.Frame(main_root)
            y_sum = 0
            y_frame = Frame(main_root)
            Label(year_frame,text=year,font=FONT).grid(row=0,column=0)
            for m,(month,days) in enumerate(months.items()):
                month_frame = Frame(y_frame)
                m_sum = 0
                m_frame = Frame(y_frame)
                Label(month_frame,text=f'{months_dict[month[:-1]].capitalize()} {year}',font=FONT).grid(row=0,column=0)
                for k,(day,records) in enumerate(days.items()):
                    day_frame = Frame(m_frame)
                    d_sum = 0
                    d_frame = Frame(m_frame,highlightbackground="blue", highlightthickness=2)
                    Label(day_frame,text=f'{day}.{month[:-1]}.{year}',font=FONT).grid(row=0,column=0)
                    for num,(id_,summ,descr) in enumerate(records):
                        Label(d_frame,text=descr,font=FONT).grid(row=num,column=0)
                        Label(d_frame,text=f'{summ} р.',font=FONT).grid(row=num,column=1)
                        Button(d_frame,text='Удалить',command=lambda args=(id_,arg):self.delete(*args)).grid(row=num,column=2)
                        Button(d_frame,text='Редактор',command=lambda args=(id_,arg):self.editor(*args)).grid(row=num,column=3)
                        y_sum += summ
                        m_sum += summ
                        d_sum += summ
                    Label(day_frame,text=f'{d_sum} р.',font=FONT).grid(row=0,column=1)
                    d_frame.grid(row=k*2+1,column=0)
                    day_frame.grid(row=k*2,column=0)
                Label(month_frame,text=f'{m_sum} р.',font=FONT).grid(row=0,column=1)
                m_frame.grid(row=m*2+1,column=0)
                month_frame.grid(row=m*2,column=0)
            Label(year_frame,text=f'{y_sum} р.',font=FONT).grid(row=0,column=1)
            y_frame.grid(row=n*2+2,column=1)
            year_frame.grid(row=n*2+1,column=1, columnspan=12)
            Label(main_root,text='\t\t\t\t').grid(row=0,column=0) #костыль)

    def check_year(self): #проверка года, нужна, чтобы случайно не уйти далеко в прошлое или будущее)
        now = self.current_year
        first = self.years[0]
        last = self.years[-1]
        return (
            (now in range(first,last+1)))

    def visual(self,arg,year=None):
        self.show_now = arg
        if self.check_year():
            self.destroy_()
        if not year:
            year = self.current_year
        else:
            self.current_year = year
        if (arg,) in types:
            self.cur.execute(f'''
            select sum(RECORDS.summa),strftime('%m',RECORDS.date)
            from RECORDS join TYPES on RECORDS.type=TYPES.id
            where TYPES.title = '{arg}' and strftime('%Y',RECORDS.date) = '{year}'
            group by strftime('%Y%m',RECORDS.date)
            ''')
        else:
            self.show_now = 'Прибыль/убыток'
        self.plot_graph()

    def setWidget(self): #кнопки перемещения по годам
        button_frame = Frame(self)
        self.lbutton1 = ttk.Button(button_frame, style='Left1.TButton',
                                   text='',command=lambda arg=int(self.current_year)-1:self.visual(self.show_now,arg))
        self.lbutton2 = ttk.Button(button_frame, style='Left2.TButton',
                                   text='',command=lambda arg=int(self.current_year)+1:self.visual(self.show_now,arg))
        if self.current_year > self.years[0]:
            self.lbutton1.grid(row=0,column=0)
        if self.current_year != self.years[-1]:
            self.lbutton2.grid(row=0,column=1)
        button_frame.grid(row=0,column=0)

    def plot_graph(self): #визуализация данных
        self.setWidget()
        arg = self.show_now
        months_ = {i:0 for i in months_dict.values()}
        if arg != 'Прибыль/убыток':
            for s,m in self.cur.fetchall():
                months_[months_dict[m]] = s
        else:
            self.cur.execute(f'''select sum(RECORDS.summa),strftime('%m',RECORDS.date)
    from RECORDS join TYPES on RECORDS.type=TYPES.id
    where strftime('%Y',RECORDS.date) = '{self.current_year}' and TYPES.title='Доход'
    group by strftime('%m',RECORDS.date)''')
            for s,m in self.cur.fetchall():
                months_[months_dict[m]] += s
            self.cur.execute(f'''select sum(RECORDS.summa),strftime('%m',RECORDS.date)
    from RECORDS join TYPES on RECORDS.type=TYPES.id
    where strftime('%Y',RECORDS.date) = '{self.current_year}' and TYPES.title='Расход'
    group by strftime('%m',RECORDS.date)''')
            for s,m in self.cur.fetchall():
                months_[months_dict[m]] -= s
        figure = plt.figure(figsize=(12, 5))
        plt.bar(x=months_.keys(),height=months_.values())

        # create FigureCanvasTkAgg object
        frame = Frame(self)
        figure_canvas = FigureCanvasTkAgg(figure, frame)
        figure_canvas.draw()
        figure_canvas.get_tk_widget().grid(row=0,column=0)
        frame.grid(row=1,column=0)

        plt.title(f'{arg} за {self.current_year} год')
        plt.subplots_adjust(left=0.07,right=0.82,top=0.94,bottom=0.06)
        plt.ylabel('Сумма')
        root = Frame(frame)
        root.grid(row=1,column=0)
        NavigationToolbar2Tk(figure_canvas, root)

    def destroy_(self): #очищение интерфейса
        for widget in self.winfo_children():
            if type(widget) != Menu:
                widget.destroy()

    def add_form(self): #форма добавления записи
        self.destroy_()
        self.types = ttk.Combobox(self,values=types_,font=FONT)
        self.calendar = DateEntry(master=self,selectmode='day',font=FONT)
        self.descr = Entry(self,font=FONT)
        self.summ = Entry(self,font=FONT)

        Label(self,text='Дата',font=FONT).grid(row=0,column=1)
        Label(self,text='Описание',font=FONT).grid(row=1,column=1)
        Label(self,text='Сумма, р.',font=FONT).grid(row=2,column=1)
        Label(self,text='Тип записи',font=FONT).grid(row=3,column=1)

        self.calendar.grid(row=0,column=2)
        self.descr.grid(row=1,column=2)
        self.summ.grid(row=2,column=2)
        self.types.grid(row=3,column=2)

        Button(master=self,text='Добавить',command=self.add,font=FONT).grid(row=4,column=1)
        Label(self,text='\t\t\t\t').grid(row=0,column=0) #костыль)

    def add(self): #добавление записи
        self.cur.execute('''INSERT INTO RECORDS (summa,descr,date,type) VALUES(?,?,?,?)''',
                         (float(self.summ.get()),
                          self.descr.get(),
                          self.calendar.get_date(),
                          types_.index(self.types.get())+1
                          )
                        )
        con.commit()
        try:
            self.current_year
        except AttributeError:
            self.current_year = self.calendar.get_date().year
            self.init_forms()

    def setStyle(self): #создание стилей (для создания кнопок-стрелок)
        style = ttk.Style()
        style.configure('YFrame',bg='navy')
        #Approach 1
        #==========
        # Define style Left.TButton to show the following elements: leftarrow,
        #  padding, label 
        style.layout(
            'Left1.TButton',[
                ('Button.focus', {'children': [
                    ('Button.leftarrow', None),
                    ('Button.padding', {'sticky': 'nswe', 'children': [
                        ('Button.label', {'sticky': 'nswe'}
                         )]}
                     )]}
                 )]
            )
        #Change 3 options of the "arrow" element in style "Left.TButton"
        style.configure('Left1.TButton',
                        font=('','20','bold'), width=9)
        #Approach 2
        #==========
        style.layout(
            'Left2.TButton',[
                ('Button.focus', {'children': [
                    ('Button.rightarrow', None), #arrow button!
                    ('Button.padding', {'sticky': 'nswe', 'children': [
                        ('Button.label', {'sticky': 'nswe'}
                         )]}
                     )]}
                 )]
            )
        style.configure('Left2.TButton',font=('','20','bold'), width=9, arrowcolor='white')

    def _on_mousewheel(self, event): #скроллинг мышкой
        self.canvas.yview_scroll(-1*(int(event.delta/120)), "units")

    def delete(self,id_,arg): #удаление
        self.cur.execute(f'delete from RECORDS where id={id_}')
        con.commit()
        self.show_records(arg)

    def editor(self,id_,arg): #редактор записи
        top = Toplevel()
        top.title('Редактор')
        self.cur.execute('select * from RECORDS where id=?',(id_,))
        record = self.cur.fetchone() #id,summa,descr,date,type

        year,month,day = map(int,record[-2].split('-'))

        self.editor_types = ttk.Combobox(top,values=types_,font=FONT)
        self.editor_types.current(record[-1]-1)

        self.editor_calendar = DateEntry(master=top,selectmode='day',font=FONT,year=year,month=month,day=day)
        self.editor_descr = Entry(top,font=FONT)
        self.editor_descr.insert(0, record[2])
        self.editor_summ = Entry(top,font=FONT)

        self.editor_summ.insert(0, record[1])

        Label(top,text='Дата',font=FONT).grid(row=0,column=1)
        Label(top,text='Описание',font=FONT).grid(row=1,column=1)
        Label(top,text='Сумма, р.',font=FONT).grid(row=2,column=1)
        Label(top,text='Тип записи',font=FONT).grid(row=3,column=1)

        self.editor_calendar.grid(row=0,column=2)
        self.editor_descr.grid(row=1,column=2)
        self.editor_summ.grid(row=2,column=2)
        self.editor_types.grid(row=3,column=2)

        Button(master=top,text='Сохранить',command=lambda arg=id_:self.save(arg),font=FONT).grid(row=4,column=1)
        Button(master=top,text='Отменить',command=top.destroy,font=FONT).grid(row=4,column=2)

        Label(top,text='\t').grid(row=0,column=0) #костыль)

    def save(self,id_): #редактирование записи
        d = {'type':types_.index(self.editor_types.get())+1,'date':self.editor_calendar.get_date(),
             'descr':self.editor_descr.get(),'summa':float(self.editor_summ.get())}
        self.cur.execute(f"""UPDATE RECORDS
                         SET type = {d['type']}, date = '{d['date']}', descr = '{d['descr']}', summa = {d['summa']}
                         where id={id_}""")
        con.commit()
        self.show_records(self.editor_types.get())

    def quit_me(self): #чтобы программа закрывалась, если пользователь посмотрел графики
        self.quit()
        self.destroy()

if __name__ == '__main__':
    app = App()
    app.mainloop()
    app.cur.close()
