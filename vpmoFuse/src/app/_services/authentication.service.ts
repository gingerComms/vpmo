import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { map, filter, scan } from 'rxjs/operators';
import { User } from '../user/user';
import { appConfig } from '../app.config';
import { BehaviorSubject } from 'rxjs/index';
import { of } from 'rxjs';
import { Router } from '@angular/router';

@Injectable()

export class AuthenticationService {
    tempUser: any;
    private user = new BehaviorSubject<any>('');
    currentUser = this.user.asObservable();
    private loggedIn = new BehaviorSubject<boolean>(false);
    userLoggedIn = this.loggedIn.asObservable();

    constructor(private http: HttpClient, private router: Router) { }

    get isLoggedIn() {
        return this.loggedIn.asObservable(); // {2}
    }

    login(email: string, password: string) {
        console.log('Logging In...');
        return this.http.post<any>(appConfig.apiUrl + '/users/login', { email: email, password: password })
            .pipe(map(user => {
                // login successful if there's a jwt token in the response
                if (user && user.token) {
                    // store user details and jwt token in local storage to keep user logged in between page refreshes
                    localStorage.setItem('currentUser', JSON.stringify(user));
                    this.user.next(JSON.parse(localStorage.getItem('currentUser')));
                    this.loggedIn.next(true);
                    return user;
                } else {
                    console.log('could not log in, either email or password is wrong!');
                    localStorage.removeItem('currentUser');
                    throw new Error('Email and/or Password is wrong!');
                }
            }));
    }

    logout() {
        // remove user from local storage to log user out
        localStorage.removeItem('currentUser');
        this.loggedIn.next(false);
        this.router.navigate(['/user/login']);
    }

    // isLoggedIn() {
    //     // return false;
    //     return this.userLoggedIn;
    // }

    updateLocalStorage (fullname, username, email) {
        this.tempUser = JSON.parse(localStorage.getItem('currentUser'));
        this.tempUser.fullname = fullname;
        this.tempUser.username = username;
        this.tempUser.email = email;
        localStorage.setItem('currentUser', JSON.stringify(this.tempUser));
        this.user.next(JSON.parse(localStorage.getItem('currentUser')));
        return this.user;
    }

}
