import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/observable/throw';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/do';
import { appConfig } from '../app.config';

import { IProject } from './project';
import { HttpErrorResponse } from '@angular/common/http/src/response';

@Injectable()
export class ProjectService {
  private _projectUrl = 'http://127.0.0.1:8000/vpmoapp/projects';

  constructor(private http: HttpClient) { }

  getProjects(): Observable<IProject[]> {
    return this.http.get<IProject[]>(this._projectUrl)
        .do(data => console.log('All: ' + JSON.stringify(data)))
        .catch(this.handleError);
  }

  private handleError(err: HttpErrorResponse) {
    console.log(err.message);
    return Observable.throw(err.message);
  }

  create(project: IProject) {
    return this.http.post(appConfig.apiUrl + '/projects/add', project);
  }
}
